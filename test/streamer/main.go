package main

import (
	"fmt"
	"os"
	"os/exec"
)

func main() {
	multicastAddr := "239.255.0.1"
	port := "1234"
	udpURL := fmt.Sprintf("udp://%s:%s", multicastAddr, port)

	cmd := exec.Command(
		"ffmpeg",
		"-re", // input option
		"-f", "lavfi",
		"-i", "smptebars=size=640x480:rate=30",
		"-c:v", "libx264",
		"-pix_fmt", "yuv420p",
		"-tune", "zerolatency",
		"-f", "mpegts",
		udpURL,
	)

	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	fmt.Printf("Streaming test pattern to %s...\n", udpURL)

	if err := cmd.Run(); err != nil {
		fmt.Println("Error running FFmpeg:", err)
		return
	}

	fmt.Println("Streaming finished.")
}
