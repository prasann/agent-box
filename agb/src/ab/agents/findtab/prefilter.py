"""Rule-based URL pre-filter for FindTab.

Runs before the LLM classifier to quickly categorize obvious URLs,
reducing API calls and speeding up the indexing pipeline.
"""
import os
from fnmatch import fnmatch
from typing import Optional, Literal
from urllib.parse import urlparse
import yaml
from pydantic import BaseModel
from .models import HistoryEntry


class PreFilterResult(BaseModel):
    """Result of pre-filtering."""
    decision: Literal['save', 'skip', 'unknown']
    reason: str


# Domain patterns matched with fnmatch against the full hostname
SKIP_DOMAINS = [
    ("mail.google.com", "email"),
    ("outlook.live.com", "email"),
    ("outlook.office.com", "email"),
    ("outlook.office365.com", "email"),
    ("mail.*", "email"),
    ("*.bank.*", "banking"),
    ("*.chase.com", "banking"),
    ("*.wellsfargo.com", "banking"),
    ("*.bankofamerica.com", "banking"),
    ("*.citi.com", "banking"),
    ("*.capitalone.com", "banking"),
    ("*.paypal.com", "financial"),
    ("*.venmo.com", "financial"),
    ("*.mint.com", "financial"),
    ("*.amazon.*", "shopping"),
    ("*.flipkart.com", "shopping"),
    ("twitter.com", "social feed"),
    ("x.com", "social feed"),
    ("facebook.com", "social feed"),
    ("www.facebook.com", "social feed"),
    ("instagram.com", "social feed"),
    ("www.instagram.com", "social feed"),
]

# Full URL patterns matched with fnmatch against the full URL
SKIP_URL_PATTERNS = [
    # Auth pages
    ("*/login*", "auth page"),
    ("*/signin*", "auth page"),
    ("*/sign-in*", "auth page"),
    ("*/oauth*", "auth page"),
    ("*/auth/*", "auth page"),
    ("*/sso/*", "auth page"),
    # Account/financial paths
    ("*/account*", "account page"),
    ("*/balance*", "banking page"),
    ("*/statement*", "banking page"),
    # Shopping paths
    ("*/cart*", "shopping"),
    ("*/checkout*", "shopping"),
    ("*/orders*", "shopping"),
    # Social feeds (not individual posts)
    ("*twitter.com/home*", "social feed"),
    ("*x.com/home*", "social feed"),
    ("*linkedin.com/feed*", "social feed"),
    # Search results
    ("*google.com/search*", "search results"),
    ("*bing.com/search*", "search results"),
    ("*duckduckgo.com/?q=*", "search results"),
    ("*duckduckgo.com/*q=*", "search results"),
]

# Scheme-based skips (checked with str.startswith)
SKIP_SCHEMES = [
    ("chrome://", "browser internal"),
    ("edge://", "browser internal"),
    ("about:", "browser internal"),
    ("chrome-extension://", "browser extension"),
    ("file://", "local file"),
]

# Localhost patterns
SKIP_LOCALHOST = [
    ("localhost", "local dev"),
    ("127.0.0.1", "local dev"),
    ("0.0.0.0", "local dev"),
]

SAVE_DOMAINS = [
    ("*.readthedocs.io", "documentation"),
    ("*.stackexchange.com", "Q&A"),
]

SAVE_URL_PATTERNS = [
    # Tech blogs
    ("*medium.com/@*", "tech blog"),
    ("*medium.com/*/*", "tech blog"),
    ("*dev.to/*", "tech blog"),
    ("*.substack.com/p/*", "newsletter post"),
    ("*hashnode.dev/*", "tech blog"),
    ("*blog.*/*", "blog"),
    # Documentation
    ("*docs.*/*", "documentation"),
    ("*developer.*/*", "developer docs"),
    ("*learn.microsoft.com/*", "documentation"),
    # Code
    ("*github.com/*/blob/*", "source code"),
    ("*github.com/*/tree/*", "code tree"),
    ("*github.com/*/*/issues/*", "GitHub issue"),
    ("*github.com/*/*/pull/*", "GitHub PR"),
    ("*github.com/*/*/discussions/*", "GitHub discussion"),
    # Q&A
    ("*stackoverflow.com/questions/*", "Q&A"),
    ("*.stackexchange.com/questions/*", "Q&A"),
    # Discussions
    ("*news.ycombinator.com/item*", "HN discussion"),
    ("*reddit.com/r/*/comments/*", "Reddit discussion"),
    # Reference
    ("*wikipedia.org/wiki/*", "encyclopedia"),
    ("*arxiv.org/abs/*", "research paper"),
    ("*arxiv.org/pdf/*", "research paper"),
]


class URLPreFilter:
    """Rule-based URL pre-filter.

    Quickly categorizes URLs as save/skip/unknown using pattern matching,
    before falling back to LLM classification for unknowns.
    """

    def __init__(self, custom_rules_path: Optional[str] = None):
        """Load built-in rules and optional user rules.

        Args:
            custom_rules_path: Path to custom rules YAML file (e.g. ~/.agb/findtab/rules.yaml)
        """
        self.custom_skip: list[tuple[str, str]] = []
        self.custom_save: list[tuple[str, str]] = []

        if custom_rules_path:
            self._load_custom_rules(os.path.expanduser(custom_rules_path))

    def _load_custom_rules(self, path: str) -> None:
        """Load custom rules from a YAML file."""
        if not os.path.exists(path):
            return

        try:
            with open(path) as f:
                data = yaml.safe_load(f) or {}

            for rule in data.get("skip", []):
                self.custom_skip.append((rule["pattern"], rule.get("reason", "custom skip rule")))
            for rule in data.get("save", []):
                self.custom_save.append((rule["pattern"], rule.get("reason", "custom save rule")))
        except Exception as e:
            print(f"Warning: Failed to load custom rules from {path}: {e}")

    def classify(self, url: str, title: str) -> PreFilterResult:
        """Classify a single URL.

        Args:
            url: The full URL
            title: The page title

        Returns:
            PreFilterResult with decision and reason
        """
        # Scheme-based skips (browser internals, file://)
        for scheme, reason in SKIP_SCHEMES:
            if url.startswith(scheme):
                return PreFilterResult(decision="skip", reason=reason)

        # Localhost
        for pattern, reason in SKIP_LOCALHOST:
            if url.startswith(f"http://{pattern}") or url.startswith(f"https://{pattern}"):
                return PreFilterResult(decision="skip", reason=reason)

        # Empty or trivial titles
        if not title or not title.strip():
            return PreFilterResult(decision="skip", reason="empty title")

        try:
            parsed = urlparse(url)
            hostname = parsed.hostname or ""
        except Exception:
            return PreFilterResult(decision="unknown", reason="unparseable URL")

        if self._title_is_just_domain(title, hostname):
            return PreFilterResult(decision="skip", reason="title is just domain name")

        # Custom rules take priority over built-in rules
        for pattern, reason in self.custom_skip:
            if fnmatch(url, pattern) or fnmatch(hostname, pattern):
                return PreFilterResult(decision="skip", reason=reason)

        for pattern, reason in self.custom_save:
            if fnmatch(url, pattern) or fnmatch(hostname, pattern):
                return PreFilterResult(decision="save", reason=reason)

        # Built-in domain skips
        for pattern, reason in SKIP_DOMAINS:
            if fnmatch(hostname, pattern):
                return PreFilterResult(decision="skip", reason=reason)

        # Built-in URL pattern skips
        for pattern, reason in SKIP_URL_PATTERNS:
            if fnmatch(url, pattern):
                return PreFilterResult(decision="skip", reason=reason)

        # Built-in domain saves
        for pattern, reason in SAVE_DOMAINS:
            if fnmatch(hostname, pattern):
                return PreFilterResult(decision="save", reason=reason)

        # Built-in URL pattern saves
        for pattern, reason in SAVE_URL_PATTERNS:
            if fnmatch(url, pattern):
                return PreFilterResult(decision="save", reason=reason)

        return PreFilterResult(decision="unknown", reason="no matching rule")

    def filter_batch(
        self, entries: list[HistoryEntry]
    ) -> tuple[list[HistoryEntry], list[HistoryEntry], list[HistoryEntry]]:
        """Split entries into (save, skip, unknown) lists.

        Args:
            entries: History entries to pre-filter

        Returns:
            Tuple of (save, skip, unknown) entry lists
        """
        save, skip, unknown = [], [], []

        for entry in entries:
            result = self.classify(entry.url, entry.title)
            if result.decision == "save":
                save.append(entry)
            elif result.decision == "skip":
                skip.append(entry)
            else:
                unknown.append(entry)

        return save, skip, unknown

    @staticmethod
    def _title_is_just_domain(title: str, hostname: str) -> bool:
        """Check if a title is just the domain name or a trivial variation."""
        title_clean = title.strip().lower()
        hostname_clean = hostname.lower()

        if not title_clean:
            return False

        # Exact match or with/without www prefix
        bare_host = hostname_clean.removeprefix("www.")
        return title_clean in (hostname_clean, bare_host)
