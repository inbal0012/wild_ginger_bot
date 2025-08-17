import re
from urllib.parse import urlparse
from dataclasses import dataclass

@dataclass
class ValidationResult:
    is_valid: bool
    platform: str
    reason: str

def validate_social_link(url):
    """
    Validate Facebook or Instagram URLs
    
    Args:
        url (str): The URL to validate
        
    Returns:
        dict: Contains 'is_valid', 'platform', and 'reason' keys
    """
    if not url or not isinstance(url, str):
        return ValidationResult(is_valid=False, platform=None, reason='URL is empty or not a string')
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove 'www.' prefix if present
        domain = re.sub(r'^www\.', '', domain)
        
        # Facebook validation
        facebook_domains = ['facebook.com', 'm.facebook.com', 'fb.com', 'fb.me']
        instagram_domains = ['instagram.com', 'instagr.am']
        
        if domain in facebook_domains:
            return validate_facebook_url(parsed)
        elif domain in instagram_domains:
            return validate_instagram_url(parsed)
        else:
            return ValidationResult(is_valid=False, platform=None, reason=f'Domain "{domain}" is not a valid Facebook or Instagram domain')
            
    except Exception as e:
        return ValidationResult(is_valid=False, platform=None, reason=f'Invalid URL format: {str(e)}')

def validate_facebook_url(parsed_url):
    """Validate Facebook-specific URL patterns"""
    path = parsed_url.path.lower()
    
    # Valid Facebook URL patterns
    facebook_patterns = [
        r'^/[a-zA-Z0-9._-]+/?$',  # Profile: /username
        r'^/pages/[^/]+/\d+/?$',  # Page: /pages/name/id
        r'^/profile\.php$',       # Profile with ID parameter
        r'^/[a-zA-Z0-9._-]+/posts/\d+/?$',  # Post
        r'^/groups/\d+/?$',       # Group
        r'^/events/\d+/?$',       # Event
        r'^/photo\.php$',         # Photo
        r'^/video\.php$',         # Video
    ]
    
    # Check if it's a profile.php with fbid parameter
    if path == '/profile.php':
        query_params = parsed_url.query
        if 'id=' in query_params or 'fbid=' in query_params:
            return ValidationResult(is_valid=True, platform='facebook', reason='Valid Facebook profile URL')
    
    # Check against patterns
    for pattern in facebook_patterns:
        if re.match(pattern, path):
            return ValidationResult(is_valid=True, platform='facebook', reason='Valid Facebook URL')
    
    return ValidationResult(is_valid=False, platform='facebook', reason='Invalid Facebook URL format')

def validate_instagram_url(parsed_url):
    """Validate Instagram-specific URL patterns"""
    path = parsed_url.path.lower()
    
    # Valid Instagram URL patterns
    instagram_patterns = [
        r'^/[a-zA-Z0-9._]+/?$',           # Profile: /username
        r'^/p/[a-zA-Z0-9_-]+/?$',        # Post: /p/post_id
        r'^/reel/[a-zA-Z0-9_-]+/?$',     # Reel: /reel/reel_id
        r'^/tv/[a-zA-Z0-9_-]+/?$',       # IGTV: /tv/video_id
        r'^/stories/[a-zA-Z0-9._]+/\d+/?$',  # Story
        r'^/explore/tags/[a-zA-Z0-9_]+/?$',  # Hashtag
    ]
    
    # Check against patterns
    for pattern in instagram_patterns:
        if re.match(pattern, path):
            return ValidationResult(is_valid=True, platform='instagram', reason='Valid Instagram URL')
    
    return ValidationResult(is_valid=False, platform='instagram', reason='Invalid Instagram URL format')

# Example usage and testing
if __name__ == "__main__":
    test_urls = [
        # Valid Facebook URLs
        "https://facebook.com/username",
        "https://www.facebook.com/pages/PageName/123456789",
        "https://facebook.com/profile.php?id=123456",
        "fb.com/username",
        
        # Valid Instagram URLs
        "https://instagram.com/username",
        "https://www.instagram.com/p/ABC123DEF",
        "instagram.com/username",
        "https://instagram.com/reel/XYZ789",
        
        # Invalid URLs
        "https://twitter.com/username",
        "not-a-url",
        "https://facebook.com/",
        "https://instagram.com/",
    ]
    
    print("Social Media Link Validation Results:")
    print("=" * 50)
    
    for url in test_urls:
        result = validate_social_link(url)
        status = "✅ VALID" if result['is_valid'] else "❌ INVALID"
        platform = result['platform'] or "Unknown"
        
        print(f"{status} | {platform.upper():10} | {url}")
        print(f"    Reason: {result['reason']}")
        print()