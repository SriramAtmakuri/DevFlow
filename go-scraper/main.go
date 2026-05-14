package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"

	"golang.org/x/net/html"
)

// ── Types ─────────────────────────────────────────────────────────────────────

type ScrapeRequest struct {
	URLs      []string `json:"urls"`
	MaxLength int      `json:"max_length"`
}

type ScrapeResult struct {
	URL     string `json:"url"`
	Content string `json:"content"`
	Success bool   `json:"success"`
	Error   string `json:"error,omitempty"`
}

type ScrapeResponse struct {
	Results []ScrapeResult `json:"results"`
	Elapsed string         `json:"elapsed"`
	Total   int            `json:"total"`
}

// ── HTML text extractor ───────────────────────────────────────────────────────

var skipTags = map[string]bool{
	"script": true, "style": true, "nav": true,
	"footer": true, "header": true, "noscript": true,
	"aside": true, "iframe": true,
}

func extractText(n *html.Node, sb *strings.Builder) {
	if n.Type == html.TextNode {
		text := strings.TrimSpace(n.Data)
		if text != "" {
			sb.WriteString(text)
			sb.WriteString("\n")
		}
		return
	}
	if n.Type == html.ElementNode && skipTags[n.Data] {
		return
	}
	for c := n.FirstChild; c != nil; c = c.NextSibling {
		extractText(c, sb)
	}
}

// ── Scraper ───────────────────────────────────────────────────────────────────

var httpClient = &http.Client{
	Timeout: 10 * time.Second,
}

func scrapeURL(url string, maxLength int) ScrapeResult {
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return ScrapeResult{URL: url, Success: false, Error: err.Error()}
	}
	req.Header.Set("User-Agent", "Mozilla/5.0 (compatible; DevFlow/2.0)")
	req.Header.Set("Accept", "text/html,application/xhtml+xml")

	resp, err := httpClient.Do(req)
	if err != nil {
		return ScrapeResult{URL: url, Success: false, Error: err.Error()}
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(io.LimitReader(resp.Body, 2*1024*1024)) // 2MB cap
	if err != nil {
		return ScrapeResult{URL: url, Success: false, Error: err.Error()}
	}

	doc, err := html.Parse(strings.NewReader(string(body)))
	if err != nil {
		return ScrapeResult{URL: url, Success: false, Error: "html parse error"}
	}

	var sb strings.Builder
	extractText(doc, &sb)

	text := sb.String()
	// Collapse excessive blank lines
	lines := strings.Split(text, "\n")
	var cleaned []string
	for _, l := range lines {
		if t := strings.TrimSpace(l); t != "" {
			cleaned = append(cleaned, t)
		}
	}
	text = strings.Join(cleaned, "\n")

	if maxLength > 0 && len(text) > maxLength {
		text = text[:maxLength] + "..."
	}

	return ScrapeResult{URL: url, Content: text, Success: true}
}

// ── Handlers ──────────────────────────────────────────────────────────────────

func handleScrape(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req ScrapeRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "invalid json", http.StatusBadRequest)
		return
	}
	if len(req.URLs) == 0 {
		http.Error(w, "urls required", http.StatusBadRequest)
		return
	}
	if req.MaxLength == 0 {
		req.MaxLength = 5000
	}
	// Cap at 20 URLs per request
	if len(req.URLs) > 20 {
		req.URLs = req.URLs[:20]
	}

	start := time.Now()
	results := make([]ScrapeResult, len(req.URLs))

	var wg sync.WaitGroup
	for i, url := range req.URLs {
		wg.Add(1)
		go func(idx int, u string) {
			defer wg.Done()
			results[idx] = scrapeURL(u, req.MaxLength)
		}(i, url)
	}
	wg.Wait()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(ScrapeResponse{
		Results: results,
		Elapsed: fmt.Sprintf("%.2fms", float64(time.Since(start).Microseconds())/1000),
		Total:   len(results),
	})
}

func handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "ok",
		"service": "devflow-go-scraper",
		"version": "1.0.0",
	})
}

// ── Main ──────────────────────────────────────────────────────────────────────

func main() {
	port := os.Getenv("SCRAPER_PORT")
	if port == "" {
		port = "8001"
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/scrape", handleScrape)
	mux.HandleFunc("/health", handleHealth)

	log.Printf("DevFlow Go scraper listening on :%s", port)
	if err := http.ListenAndServe(":"+port, mux); err != nil {
		log.Fatalf("server error: %v", err)
	}
}
