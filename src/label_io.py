"""Read published label tables without changing their stored contents."""
from pathlib import Path as _ReleasePath
import sys as _release_sys
_release_root = next(_p for _p in _ReleasePath(__file__).resolve().parents if (_p / 'runtime_config.py').is_file())
_release_sys.path.insert(0, str(_release_root))
from runtime_config import project_path


from pathlib import Path

import pandas as pd


LABELS_DIR = Path(project_path("labels", ""))

# Format aliases for the seven existing media categories, not new score labels.
MEDIA_LABEL_ALIASES = {
    "extreme left": "Extreme Bias Left",
    "left": "Left",
    "left leaning": "Left Leaning",
    "center": "Center",
    "right leaning": "Right Leaning",
    "right": "Right",
    "extreme right": "Extreme Bias Right",
}


def label_path(filename):
    """Resolve a bundled label filename independently of the working directory."""
    return LABELS_DIR / filename


def read_label_csv(file_path, *, media_domains=False):
    """Read IDs as strings; adapt only documented encoding/domain-label formats.

    Explicit paths are used as given: a missing file never falls back to another
    dictionary. Duplicate rows and unrecognized labels retain their old handling
    in the calling scorer. No CSV is rewritten.
    """
    try:
        table = pd.read_csv(file_path, dtype=str, index_col=False, encoding="utf-8-sig")
    except UnicodeDecodeError:
        table = pd.read_csv(file_path, dtype=str, index_col=False, encoding="gb18030")

    if media_domains:
        if "Url" not in table.columns and "domain" in table.columns:
            table = table.rename(columns={"domain": "Url"})
        if "bias" in table.columns:
            table["bias"] = table["bias"].replace(MEDIA_LABEL_ALIASES)
    return table


def politician_id_scores_from_usernames(username_file, mapping_file):
    """Use the author-selected original labels and an external ID/username map.

    Username matching retains exact case and whitespace trimming. Label columns
    in the mapping file are ignored. Ambiguous ID-to-username maps are rejected.
    """
    labels = read_label_csv(username_file)
    if not {"username", "bias"}.issubset(labels.columns):
        raise ValueError("Original politician labels require username,bias")
    score = labels["bias"].map({"Left": -1, "Center": 0, "Right": 1})
    names = labels["username"].astype("string").str.strip()
    valid = names.notna() & names.ne("") & score.notna()
    lookup = dict(zip(names[valid], score[valid].astype(int)))
    mapping = read_label_csv(mapping_file)
    id_col = next((c for c in ("user_id", "retweet_origin_user_id", "id_str") if c in mapping.columns), None)
    name_col = next((c for c in ("username", "screen_name", "Username") if c in mapping.columns), None)
    if id_col is None or name_col is None:
        raise ValueError("ID mapping requires user_id,username (or documented field aliases)")
    ids = mapping[id_col].astype("string").str.strip()
    names = mapping[name_col].astype("string").str.strip()
    pairs = pd.DataFrame({"user_id": ids, "username": names}).dropna()
    pairs = pairs[(pairs.user_id != "") & (pairs.username != "")]
    if (pairs.groupby("user_id").username.nunique() > 1).any():
        raise ValueError("One ID maps to multiple usernames; supply a resolved ID mapping")
    matched = pairs.username.map(lookup)
    print(f"Politician ID mapping: {len(pairs)} rows, {int(matched.notna().sum())} exact username matches")
    return dict(zip(pairs.loc[matched.notna(), "user_id"], matched[matched.notna()].astype(int)))


def read_exposure_csv(file_path):
    """Adapt named exposure columns to the existing positional extraction loop.

    This only rearranges fields. No record is selected, dropped, duplicated or
    scored here. Legacy 20-column inputs are also accepted as supplied.
    """
    table = pd.read_csv(file_path, dtype=str)
    author_fields = {"retweeted_user_id", "retweet_origin_user_id", "quoted_origin_user_id"}
    if author_fields.issubset(table.columns):
        legacy = pd.DataFrame(index=table.index, columns=[f"field_{i}" for i in range(20)], dtype=object)
        positions = {2: "retweeted_user_id", 8: "retweet_expanded_urls_array", 9: "retweet_origin_user_id",
                     18: "quoted_expanded_urls_array", 19: "quoted_origin_user_id"}
        for position, field in positions.items():
            if field in table.columns:
                legacy.iloc[:, position] = table[field]
        return legacy
    if len(table.columns) < 20:
        raise ValueError("Supply named exposure fields or the documented legacy 20-column table")
    return table
