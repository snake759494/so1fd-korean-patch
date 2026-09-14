"""Apply Review 10 with input, patch and output hash verification."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys

SOURCE_SIZE = 1162182656
SOURCE_MD5 = 'a7b86fa9e5dfa394488e373e4872beb4'
SOURCE_SHA = '5a3568fc8c2d3b2fed2cd468dafcde80bad72689794812f9159bfd18554c50cc'
PATCH_SHA = '16421bc59e978fa1bcf7dee25bfacd99f0edce34035981f55cba95a5e456ba12'
OUTPUT_SHA = '3dc5acf84ce56927199d2e9c14ead14aaed89305e88486febb96154766c9dbf7'

def digest(path, kind='sha256'):
    h = hashlib.new(kind)
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('xdelta', 'source', 'patch', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    source, patch, output, exe = (p.resolve() for p in (args.source, args.patch, args.output, args.xdelta))
    if output.exists() or output in (source, patch, exe):
        raise ValueError('Output must be a new file, different from all inputs.')
    if source.stat().st_size != SOURCE_SIZE or digest(source, 'md5') != SOURCE_MD5 or digest(source) != SOURCE_SHA:
        raise ValueError('Original ISO hash mismatch. Use the unmodified Japanese ISO listed in README.')
    if digest(patch) != PATCH_SHA:
        raise ValueError('Patch SHA-256 mismatch.')
    print('Input and patch verified. Applying...', flush=True)
    # Reserve a new file atomically. Stream decoded output into it, never overwrite an existing path.
    with output.open('xb') as out:
        subprocess.run([str(exe), '-d', '-c', '-s', str(source), str(patch)], stdout=out, check=True)
    if output.stat().st_size != SOURCE_SIZE or digest(output) != OUTPUT_SHA:
        raise ValueError('Output verification failed. Do not use the resulting file.')
    print('PASS: output SHA-256 = ' + OUTPUT_SHA)

if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        sys.exit(1)
