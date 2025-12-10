package main

import (
    "fmt"
    "io"
    "log"
    "os/exec"
    "time"
)

// ChannelConfig holds the settings for the stream
type ChannelConfig struct {
    Name      string
    IP        string
    Port      string
    Provider  string
    ServiceID string
    Playlist  []string // List of YouTube URLs
}

func main() {
    // 1. Define the Single Channel
    myChannel := ChannelConfig{
        Name:      "My YouTube TV",
        IP:        "239.255.0.1",
        Port:      "1234",
        Provider:  "Custom Broadcast",
        ServiceID: "101",
        Playlist: []string{
            "https://www.youtube.com/watch?v=aqz-KE-bpKQ", // Example: Big Buck Bunny
            "https://www.youtube.com/watch?v=LXb3EKWsInQ", // Example: 4K Costa Rica
            // Add more URLs here
        },
    }

    fmt.Println("--- Starting YouTube IPTV Simulator ---")
    fmt.Printf("Broadcasting to udp://%s:%s\n", myChannel.IP, myChannel.Port)

    // 2. Loop Forever (24/7 Channel Logic)
    for {
        for _, videoURL := range myChannel.Playlist {
            fmt.Printf("[NEXT UP] Playing: %s\n", videoURL)
            err := streamVideo(myChannel, videoURL)
            if err != nil {
                log.Printf("[ERROR] Failed to stream video: %v\n", err)
                // Sleep briefly to prevent tight loop crashing on bad internet
                time.Sleep(2 * time.Second)
            }
        }
        fmt.Println("[PLAYLIST END] Looping back to start...")
    }
}

func streamVideo(config ChannelConfig, youtubeURL string) error {
    udpURL := fmt.Sprintf("udp://%s:%s?pkt_size=1316", config.IP, config.Port)

    // --- COMMAND 1: yt-dlp ---
    // We stream the data to Stdout ("-o -").
    // We force a format compatible with streaming to prevent waiting for merges.
    ytCmd := exec.Command("yt-dlp", "-o", "-", youtubeURL)

    // Create a pipe to connect yt-dlp output to ffmpeg input
    pipeReader, pipeWriter := io.Pipe()
    ytCmd.Stdout = pipeWriter
    ytCmd.Stderr = nil // Ignore yt-dlp progress logs for cleaner output

    // --- COMMAND 2: ffmpeg ---
    ffmpegCmd := exec.Command(
        "ffmpeg",
        "-re",        // Read input at native frame rate
        "-i", "pipe:0", // Read from Standard Input (the pipe)

        // Video Encoding
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-tune", "zerolatency",
        "-maxrate", "3000k", // Limit bitrate to keep UDP stable
        "-bufsize", "6000k",
        "-pix_fmt", "yuv420p",
        "-g", "60", // Keyframe interval (2 seconds at 30fps)

        // FILTER: Scale everything to 720p.
        // This is CRITICAL. If you don't scale, the stream crashes
        // when switching between a 1080p video and a 4k video.
        "-vf", "scale=1280:720",

        // Audio Encoding (Must re-encode as AAC for TS compliance)
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",

        // Output Format
        "-f", "mpegts",
        "-mpegts_service_id", config.ServiceID,
        "-metadata", "service_name="+config.Name,
        "-metadata", "service_provider="+config.Provider,

        udpURL,
    )

    // Connect the read end of the pipe to ffmpeg's Stdin
    ffmpegCmd.Stdin = pipeReader

    // Set up output handling for FFmpeg (optional, helps debug)
    // ffmpegCmd.Stdout = os.Stdout
    // ffmpegCmd.Stderr = os.Stderr

    // Start yt-dlp
    if err := ytCmd.Start(); err != nil {
        return fmt.Errorf("could not start yt-dlp: %w", err)
    }

    // Start ffmpeg
    if err := ffmpegCmd.Start(); err != nil {
        // If ffmpeg fails, kill yt-dlp to clean up
        ytCmd.Process.Kill()
        return fmt.Errorf("could not start ffmpeg: %w", err)
    }

    // Wait for yt-dlp to finish downloading
    go func() {
        ytCmd.Wait()
        pipeWriter.Close() // Close the pipe so FFmpeg knows input is done
    }()

    // Wait for FFmpeg to finish processing
    if err := ffmpegCmd.Wait(); err != nil {
        return fmt.Errorf("ffmpeg exited with error: %w", err)
    }

    return nil
}