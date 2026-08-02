package health

import "net/http"

func LoadHealth() {
	_, _ = http.Get("http://service/health")
}
