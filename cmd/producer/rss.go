package producer

import (
	"github.com/mmcdole/gofeed"
)

func FetchRSS(url string) ([]*gofeed.Item, error) {
	fp := gofeed.NewParser()
	feed, err := fp.ParseURL(url)
	if err != nil {
		return nil, err
	}
	return feed.Items, nil
}
