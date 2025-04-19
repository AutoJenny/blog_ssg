import frontmatter
import yaml
import re

def test_frontmatter_lib():
    print("Testing with frontmatter library:")
    try:
        with open('posts/kilt-evolution.md', 'r') as f:
            post = frontmatter.load(f)
            print("Success! Metadata found:", bool(post.metadata))
            print("Keys:", list(post.metadata.keys()))
    except Exception as e:
        print("Error with frontmatter lib:", str(e))

def test_regex_yaml():
    print("\nTesting with regex + yaml:")
    try:
        with open('posts/kilt-evolution.md', 'r') as f:
            content = f.read()
            front_matter_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
            if front_matter_match:
                front_matter = front_matter_match.group(1)
                metadata = yaml.safe_load(front_matter)
                print("Success! Metadata found:", bool(metadata))
                print("Keys:", list(metadata.keys()))
            else:
                print("No front matter match found with regex")
    except Exception as e:
        print("Error with regex+yaml:", str(e))

if __name__ == "__main__":
    test_frontmatter_lib()
    test_regex_yaml() 