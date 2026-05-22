import pandas as pd, json

class GlobalNewsNLP:
    def fetch_global_news_feed(self):
        # 외신 및 펜타곤 공시 핵심 데이터 수집 레이어 시뮬레이션
        return [
            {"headline": "Pentagon announces massive defense procurement contracts", "category": "Defense", "sentiment": "positive"},
            {"headline": "Global container and LNG carrier demand surges hitting multi-year highs", "category": "Shipbuilding", "sentiment": "positive"},
            {"headline": "Geopolitical alliance increases military export opportunities", "category": "Defense", "sentiment": "positive"}
        ]

    def calculate_sentiment_matrix(self, articles):
        base_score = 50.0
        defense_weight = 0.0
        ship_weight = 0.0
        
        for art in articles:
            if art["sentiment"] == "positive":
                if art["category"] == "Defense":
                    defense_weight += 20.0
                elif art["category"] == "Shipbuilding":
                    ship_weight += 25.0
                    
        return {
            "processed_articles_count": len(articles),
            "sentiment_matrix_output": {
                "방산_외신_가점": float(min(base_score + defense_weight, 100)),
                "조선_외신_가점": float(min(base_score + ship_weight, 100))
            },
            "variance_error": 0.0000
        }

if __name__ == "__main__":
    nlp = GlobalNewsNLP()
    raw_feed = nlp.fetch_global_news_feed()
    analysis = nlp.calculate_sentiment_matrix(raw_feed)
    print(json.dumps(analysis, indent=4, ensure_ascii=False))
