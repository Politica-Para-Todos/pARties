build:
	docker build -t parties .

get_candidates: build
	docker run -p 5001:5000 --rm parties python3 get_candidates.py

run: build
	docker run -p 5001:5000 --rm parties