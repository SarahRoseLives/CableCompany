package main

import (
	"fmt"
	"os/exec"
	"sync"
)

// ChannelConfig holds the settings for a single stream
type ChannelConfig struct {
	Name         string
	IP           string
	Port         string
	Provider     string
	ServiceID    string
	ColorPattern string // Just to make them visually distinct (smptebars, testsrc, color)
}

func main() {
	// Define 3 separate streams on different subnets
	channels := []ChannelConfig{
		{
			Name:         "Sports 1 HD",
			IP:           "239.255.0.1", // Standard Block .0
			Port:         "1234",
			Provider:     "CableCo Sports",
			ServiceID:    "101",
			ColorPattern: "smptebars=size=1920x1080:rate=30",
		},
		{
			Name:         "News 24 Global",
			IP:           "239.255.10.1", // Standard Block .10 (Smart Scan Beacon)
			Port:         "1234",
			Provider:     "Global News Net",
			ServiceID:    "102",
			ColorPattern: "testsrc=size=1280x720:rate=30", // 720p for variety
		},
		{
			Name:         "Cinema Classic",
			IP:           "239.192.0.1", // Org Local Block (Smart Scan Beacon)
			Port:         "1234",
			Provider:     "Movies Intl",
			ServiceID:    "103",
			ColorPattern: "color=c=blue:s=1280x720:r=30", // Solid Blue screen
		},
	}

	var wg sync.WaitGroup

	fmt.Println("--- Starting IPTV Simulator ---")
	fmt.Printf("Launching %d streams...\n", len(channels))

	for _, ch := range channels {
		wg.Add(1)
		// Launch each stream in its own goroutine
		go func(c ChannelConfig) {
			defer wg.Done()
			streamChannel(c)
		}(ch)
	}

	// Keep the main process running
	wg.Wait()
}

func streamChannel(config ChannelConfig) {
	udpURL := fmt.Sprintf("udp://%s:%s?pkt_size=1316", config.IP, config.Port)

	fmt.Printf("[STARTING] '%s' on %s (Provider: %s)\n", config.Name, udpURL, config.Provider)

	cmd := exec.Command(
		"ffmpeg",
		"-re",       // Real-time
		"-f", "lavfi", // Libavfilter input
		"-i", config.ColorPattern,

		// Video Encoding Options
		"-c:v", "libx264",
		"-preset", "ultrafast", // Use ultrafast to reduce CPU load when running 3x streams
		"-tune", "zerolatency",
		"-pix_fmt", "yuv420p",
		"-g", "60", // Keyframe interval

		// MPEG-TS Output Options
		"-f", "mpegts",
		"-mpegts_service_id", config.ServiceID,
		"-metadata", "service_name="+config.Name,
		"-metadata", "service_provider="+config.Provider,

		// Output
		udpURL,
	)

	// We don't pipe Stdout/Stderr to os.Stdout here because 3 streams mixing logs is messy.
	// We only print if there's a fatal error.
	if err := cmd.Run(); err != nil {
		fmt.Printf("[ERROR] Stream '%s' crashed: %v\n", config.Name, err)
	} else {
		fmt.Printf("[STOPPED] Stream '%s' finished.\n", config.Name)
	}
}