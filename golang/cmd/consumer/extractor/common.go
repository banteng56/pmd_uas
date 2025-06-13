package extractor

import (
	"encoding/json"
	"github.com/PuerkitoBio/goquery"
	"golang.org/x/net/html"
	"strings"
)

func getText(node *goquery.Selection) string {
	var builder strings.Builder
	
	var f func(*html.Node)
	f = func(n *html.Node) {
		if n.Type == html.TextNode {
			content := strings.TrimSpace(n.Data)
			if content != "" {
				builder.WriteString(" ")
				builder.WriteString(content)
			}
		}
		if n.FirstChild != nil {
			for c := n.FirstChild; c != nil; c = c.NextSibling {
				f(c)
			}
		}
	}

	for _, n := range node.Nodes {
		f(n)
	}

	return strings.TrimSpace(builder.String())
}

func findContentInSelector(doc *goquery.Document, selector string) (string, bool) {
	var builder strings.Builder

	if tag := doc.Find(selector); tag != nil && tag.Length() > 0 {
		tag.Each(func(i int, selection *goquery.Selection) {
			content := getText(selection)
			if len(content) > 0 {
				builder.WriteString(content)
				builder.WriteString("\n")
			}
		})
		return builder.String(), true
	}

	return "", false
}

func findAuthorInMeta(doc *goquery.Document) (string, bool) {
	if tag := doc.Find("meta[name=\"author\"]"); tag != nil {
		if author, ok := tag.Attr("content"); ok {
			return author, true
		}
	}
	return "", false
}

func findContentInLinkData(doc *goquery.Document) (string, bool) {
    scriptTags := doc.Find("script[type=\"application/ld+json\"]")
    if scriptTags.Length() == 0 {
        return "", false
    }

    var contentBuilder strings.Builder

    scriptTags.Each(func(i int, s *goquery.Selection) {
        scriptContent := s.Text()
        var jsonData map[string]interface{}
        if err := json.Unmarshal([]byte(scriptContent), &jsonData); err != nil {
            return
        }

        if articleBody, exists := jsonData["articleBody"].(string); exists {
            contentBuilder.WriteString(articleBody)
            contentBuilder.WriteString("\n")
        }
    })

    content := strings.TrimSpace(contentBuilder.String())
    if content == "" {
        return "", false
    }
    return content, true
}


func findAuthorInLinkData(doc *goquery.Document) (string, bool) {
	if tag := doc.Find("script[type=\"application/ld+json\"]"); tag != nil && tag.Length() > 0 {
		found := ""
		tag.EachWithBreak(func(i int, selection *goquery.Selection) bool {
			content := strings.TrimSpace(selection.Text())
			content = html.UnescapeString(content)

			var mapData map[string]any
			if err := json.Unmarshal([]byte(content), &mapData); err != nil {
				return true 
			}


			if authors, ok := mapData["author"].([]any); ok && len(authors) > 0 {
				if author, ok := authors[0].(map[string]any); ok {
					if name, ok := author["name"].(string); ok {
						found = name
						return false 
					}
				}
			}

			if author, ok := mapData["author"].(map[string]any); ok {
				if name, ok := author["name"].(string); ok {
					found = name
					return false 
				}
			}

			return true 
		})

		if found != "" {
			return found, true
		}
	}

	return "", false
}
