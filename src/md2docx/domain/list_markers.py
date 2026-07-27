"""Семантика маркеров списков (без Word numbering / twips)."""

# Logical style roles (mapped to Word names in outbound adapter)
LIST_ROLE_DASH = "list_dash"
LIST_ROLE_NUM = "list_number"

LIST_MARKER_EM_DASH = "\u2014"  # —
LIST_MARKER_PREFIX = "\u2014\t"  # em dash + TAB

# Back-compat aliases used by adapters until full rename
LIST_STYLE_DASH = "GostListDash"
LIST_STYLE_NUM = "GostListNumber"
