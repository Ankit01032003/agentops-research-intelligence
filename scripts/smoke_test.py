
import requests

BASE_URL = "http://127.0.0.1:8000"


def main():
    print("Testing AgentOps Research Intelligence\n")

    # 1. Health check
    response = requests.get(f"{BASE_URL}/health", timeout=10)
    response.raise_for_status()
    print("PASS: Health endpoint", response.json())

    # 2. Verify API documentation is available
    response = requests.get(f"{BASE_URL}/openapi.json", timeout=10)
    response.raise_for_status()
    api = response.json()

    paths = api.get("paths", {})
    required = ["/health", "/research", "/documents"]

    for path in required:
        if path in paths:
            print(f"PASS: Endpoint registered: {path}")
        else:
            raise AssertionError(f"Missing endpoint: {path}")

    # 3. Print available research request schema
    research = paths["/research"].get("post", {})
    request_body = research.get("requestBody", {})
    content = request_body.get("content", {})
    schema = content.get("application/json", {}).get("schema")

    print("\nResearch request schema:")
    print(schema if schema else "Inspect /docs for request details.")

    print("\nSmoke tests completed successfully.")


if __name__ == "__main__":
    main()
