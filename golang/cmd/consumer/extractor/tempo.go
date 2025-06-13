package extractor

import (
	"fmt"
	"net/http"
	"github.com/PuerkitoBio/goquery"
	"strings"
)

func ExtractTempo(url string) (string, error) {
	res, err := http.Get(url)
	if err != nil {
		return "", err
	}
	defer res.Body.Close()

	if res.StatusCode != 200 {
		return "", fmt.Errorf("Error: status code %d", res.StatusCode)
	}

	doc, err := goquery.NewDocumentFromReader(res.Body)
	if err != nil {
		return "", err
	}

	var builder strings.Builder

	if content, found := findContentInLinkData(doc); found {
		builder.WriteString(content)
		builder.WriteString("\n")
	}


	return builder.String(), nil
}
