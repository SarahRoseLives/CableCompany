package main

import (
    "fmt"
    "io"
    "log"
    "os/exec"
    "sync"
    "time"
)

// ChannelConfig holds the settings for a single stream
type ChannelConfig struct {
    Name      string
    IP        string
    Port      string
    Provider  string
    ServiceID string
    Playlist  []string // Unique playlist for this channel
}

func main() {
    // 1. Define 3 Channels with distinct Playlists
    channels := []ChannelConfig{
        {
            Name:      "Nature 4K",
            IP:        "239.255.0.1",
            Port:      "1234",
            Provider:  "Earth Cast",
            ServiceID: "101",
            Playlist: []string{
                "https://www.youtube.com/watch?v=LXb3EKWsInQ", // Costa Rica 4K
                "https://www.youtube.com/watch?v=tO01J-M3g0U", // Animals 4K
            },
        },
        {
            Name:      "Tech TV",
            IP:        "239.255.0.2",
            Port:      "1234",
            Provider:  "Geek Net",
            ServiceID: "102",
            Playlist: []string{
                "https://www.youtube.com/watch?v=jfKfPfyJRdk", // Lofi Girl (Live Stream)
                "https://www.youtube.com/watch?v=fJ9rUzIMcZQ", // Queen - Bohemian Rhapsody
            },
        },
        {
            Name:      "Action Sports",
            IP:        "239.255.0.3",
            Port:      "1234",
            Provider:  "Adrenaline",
            ServiceID: "103",
            Playlist: []string{
                "https://www.youtube.com/watch?v=qQdN4Q9I4G0", // Red Bull F1
                "https://www.youtube.com/watch?v=x76VEPXYaI0", // GoPro Hero
            },
        },
    }

    var wg sync.WaitGroup

    fmt.Println("--- Starting Multi-Channel YouTube Broadcaster ---")
    fmt.Println("--- Press Ctrl+C to Stop ---")

    for _, ch := range channels {
        wg.Add(1)
        // Launch each channel in a background Goroutine
        go func(c ChannelConfig) {
            defer wg.Done()
            runChannelLoop(c)
        }(ch)
    }

    wg.Wait()
}

// runChannelLoop handles the infinite playlist loop for a specific channel
func runChannelLoop(config ChannelConfig) {
    fmt.Printf("[%s] Channel Online -> udp://%s:%s\n", config.Name, config.IP, config.Port)

    for {
        for _, videoURL := range config.Playlist {
            fmt.Printf("[%s] Now Playing: %s\n", config.Name, videoURL)

            err := streamVideo(config, videoURL)

            if err != nil {
                log.Printf("[%s] Stream Error: %v\n", config.Name, err)
                // Sleep to prevent rapid-fire crashing if internet is down
                time.Sleep(5 * time.Second)
            }
        }
        fmt.Printf("[%s] Playlist finished. Looping...\n", config.Name)
    }
}

func streamVideo(config ChannelConfig, youtubeURL string) error {
    udpURL := fmt.Sprintf("udp://%s:%s?pkt_size=1316", config.IP, config.Port)

    // 1. yt-dlp Command
    ytCmd := exec.Command("yt-dlp", "-o", "-", youtubeURL)
    pipeReader, pipeWriter := io.Pipe()
    ytCmd.Stdout = pipeWriter
    ytCmd.Stderr = nil // discard logs

    // 2. Build the FFmpeg Filter String
    // We chain filters: Scale -> DrawText (Watermark)
    // "box=1:boxcolor=black@0.5" creates a semi-transparent background box behind the text
    filterGraph := fmt.Sprintf(
        "scale=1280:720,drawtext=text='%s':x=50:y=50:fontsize=48:fontcolor=white:box=1:boxcolor=black@0.5",
        config.Name,
    )

    // 3. FFmpeg Command
    ffmpegCmd := exec.Command(
        "ffmpeg",
        "-re",
        "-i", "pipe:0",

        // Video Settings
        "-c:v", "libx264",
        "-preset", "ultrafast", // Critical for running 3 streams at once
        "-tune", "zerolatency",
        "-maxrate", "2500k",
        "-bufsize", "5000k",
        "-pix_fmt", "yuv420p",
        "-g", "60",

        // Apply Scaling + Watermark
        "-vf", filterGraph,

        // Audio Settings
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",

        // Output Settings
        "-f", "mpegts",
        "-mpegts_service_id", config.ServiceID,
        "-metadata", "service_name="+config.Name,
        "-metadata", "service_provider="+config.Provider,
        udpURL,
    )

    ffmpegCmd.Stdin = pipeReader

    if err := ytCmd.Start(); err != nil {
        return fmt.Errorf("yt-dlp start failed: %w", err)
    }
    if err := ffmpegCmd.Start(); err != nil {
        ytCmd.Process.Kill()
        return fmt.Errorf("ffmpeg start failed: %w", err)
    }

    // Wait routine
    go func() {
        ytCmd.Wait()
        pipeWriter.Close()
    }()

    if err := ffmpegCmd.Wait(); err != nil {
        return fmt.Errorf("ffmpeg exited: %w", err)
    }

    return nil
}