import re

p = '/home/zero/tollbooth/cashier.py'
with open(p, 'r') as f:
    content = f.read()

# Find the ask_ollama function and add max_tokens parameter
# Look for the pattern where we call ask_ollama(messages)
# We need to pass max_tokens to limit output

# Strategy: Find all calls to ask_ollama and add a max_tokens parameter
# First, let's modify the ask_ollama function to accept max_tokens

# Find the ask_ollama function definition
match = re.search(r'(def ask_ollama\(messages\):.*?)(?=\ndef |\Z)', content, re.DOTALL)
if match:
    old_func = match.group(1)
    # Replace the function to accept and use max_tokens
    new_func = old_func.replace(
        'def ask_ollama(messages):',
        'def ask_ollama(messages, max_tokens=500):'
    )
    # Find where we build the payload for the API call and add max_tokens
    new_func = re.sub(
        r'payload\s*=\s*\{[^}]*"messages":\s*messages[^}]*\}',
        lambda m: m.group(0).replace('"messages": messages', f'"messages": messages, "max_tokens": max_tokens'),
        new_func
    )
    content = content.replace(old_func, new_func)
    print("PATCHED: ask_ollama now accepts max_tokens parameter")

# Now update the calls to pass max_tokens=200 for the slow endpoints
# For /uncensored_exploit_research
content = re.sub(
    r'(analysis = ask_ollama\(messages\))',
    r'analysis = ask_ollama(messages, max_tokens=200)',
    content
)

# For /post_hack_autopsy  
content = re.sub(
    r'(autopsy = ask_ollama\(messages\))',
    r'autopsy = ask_ollama(messages, max_tokens=200)',
    content
)

# For /bypass_captcha_and_scrape (the markdown generation)
content = re.sub(
    r'(markdown_content = ask_ollama\(messages\))',
    r'markdown_content = ask_ollama(messages, max_tokens=200)',
    content
)

print("PATCHED: All slow endpoints now limited to 200 tokens (faster responses)")

with open(p, 'w') as f:
    f.write(content)
