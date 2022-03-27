import os

configpath = os.path.join(
    os.environ.get('APPDATA') or
    os.environ.get('XDG_CONFIG_HOME') or
    os.path.join(os.environ['HOME'], '.config'),
    "minibuilder"
)

git_public_token = "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"