"""Restore original JSONL files and validate their manifest checksums."""
import gzip
import hashlib
import json
import os
from pathlib import Path

# Locate the manifest and archives relative to the repository, not the shell.
DATA = Path(__file__).resolve().parents[1] / 'data'


def main():
    # Expected sizes and hashes describe the original, uncompressed JSONL files.
    manifest = json.loads((DATA / 'manifests/download_manifest.json').read_text(encoding='utf-8'))
    for name, expected in manifest['raw_files'].items():
        target = DATA / 'raw' / name
        if target.exists():
            # Verify an existing file rather than overwriting it or trusting its size.
            with target.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            if target.stat().st_size != expected['bytes'] or digest != expected['sha256']:
                raise ValueError(f'Existing file differs from manifest: {target}')
            print(f'Verified existing {name}')
            continue
        # Decompress into a temporary file and hash the original bytes in one pass.
        stage = target.with_suffix(target.suffix + '.staging')
        digest = hashlib.sha256()
        with gzip.open(str(target) + '.gz', 'rb') as inp, stage.open('wb') as out:
            while block := inp.read(4 * 1024 * 1024):
                out.write(block)
                digest.update(block)
        # Do not publish a truncated or corrupted restoration.
        if stage.stat().st_size != expected['bytes'] or digest.hexdigest() != expected['sha256']:
            raise ValueError(f'Checksum mismatch: {name}')
        # Rename the validated file into its final location on the same filesystem.
        os.replace(stage, target)
        print(f'Restored and verified {name}', flush=True)


if __name__ == '__main__':
    main()
