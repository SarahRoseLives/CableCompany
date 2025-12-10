package main

import (
	"fmt"
	"os"
	"os/exec"
)

func main() {
	// Configuration
	multicastAddr := "239.255.0.1"
	port := "1234"
	udpURL := fmt.Sprintf("udp://%s:%s?pkt_size=1316", multicastAddr, port) // pkt_size=1316 is standard for MPEG-TS over UDP

	// Metadata for the "Real Deal" look
	channelName := "Sports 1 HD"
	providerName := "CableCompany"
	serviceID := "101" // This acts as the "Program Number" (PN)

	cmd := exec.Command(
		"ffmpeg",
		"-re",                                   // Read input at native frame rate (simulate live stream)
		"-f", "lavfi",                           // Input format: Libavfilter
		"-i", "testsrc=size=1920x1080:rate=30",  // Input: 1080p Test Pattern

		// Video Encoding Options
		"-c:v", "libx264",
		"-preset", "veryfast",                   // Low CPU usage for testing
		"-tune", "zerolatency",                  // Critical for live streaming
		"-pix_fmt", "yuv420p",                   // Standard pixel format for compatibility
		"-g", "60",                              // Keyframe interval (GOP) = 2 seconds at 30fps

		// MPEG-TS Output Options
		"-f", "mpegts",
		"-mpegts_service_id", serviceID,         // Sets the Program Number (PN) in the PAT
		"-metadata", "service_name="+channelName,       // The name visible in VLC/IPTV Apps
		"-metadata", "service_provider="+providerName,  // The provider visible in detailed info

		// Output
		udpURL,
	)

	// Connect stdout/stderr to see FFmpeg output in your terminal
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	fmt.Printf("Streaming '%s' (Provider: %s) to %s...\n", channelName, providerName, udpURL)
	fmt.Println("Open VLC and go to 'Media > Open Network Stream' to view.")

	if err := cmd.Run(); err != nil {
		fmt.Println("Error running FFmpeg:", err)
		return
	}

	fmt.Println("Streaming finished.")
}