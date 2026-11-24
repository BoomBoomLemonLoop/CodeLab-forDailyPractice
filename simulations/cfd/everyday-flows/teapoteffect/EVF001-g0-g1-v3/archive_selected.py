"""Build a local selective snapshot; never stage, commit, push, or delete data.

Run from any directory: python archive_selected.py. Standard library only.
ZIP paths preserve the teapoteffect subtree. SHA256 manifest describes each
included byte stream. Raw meshes/time fields are deliberately not a full backup.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
OUT = ROOT / 'archive_local'

def select():
    paths = set(BASE.glob('*.md'))
    for folder in (ROOT, ROOT / 'g3_fixed'):
        paths.update(p for p in folder.iterdir() if p.is_file() and
                     (p.suffix in {'.py', '.sh', '.md', '.json', '.txt'} or p.name == '.gitignore'))
    # Compact geometry and G2 evidence; omit dense VTK, STL and velocity CSVs.
    for folder in (ROOT/'artifacts', ROOT/'artifacts/g2_momentum',
                   ROOT/'artifacts/g2_exploratory', ROOT/'artifacts/angular_rate_5deg_s'):
        if folder.exists():
            paths.update(p for p in folder.iterdir() if p.is_file() and
                         p.suffix in {'.json', '.png', '.md', '.npz'} and p.name != 'solid_mesh.npz')
    for name in ('case1_transient_v1', 'case2_transient_v1'):
        case = ROOT/'g3_fixed/cases'/name
        paths.update(p for p in case.glob('*.json'))
        paths.update(p for p in case.glob('*.csv'))
        for folder in (case/'system', case/'constant'):
            paths.update(p for p in folder.glob('*') if p.is_file())
        for filename in ('execution_status.log', 'log.checkMesh', 'log.checkMesh.standard'):
            if (case/filename).is_file(): paths.add(case/filename)
        for pattern in ('lip_attachment.png', 'wetting_and_balance.png', 'interface_0.04.png', 'interface_0.025.png'):
            p=case/'transient_figures'/pattern
            if p.is_file(): paths.add(p)
    return sorted(paths)

def main():
    OUT.mkdir(exist_ok=True)
    selected=select()
    assert selected and (ROOT/'parameters.json') in selected
    assert (ROOT/'artifacts/angular_rate_5deg_s/parameters_5deg_s.json') in selected
    records=[]
    for p in selected:
        assert p.stat().st_size < 10_000_000, f'Review unexpectedly large file: {p}'
        records.append(dict(path=p.relative_to(BASE).as_posix(), bytes=p.stat().st_size,
                            sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    manifest=dict(scope='Selective source and evidence snapshot; not full solver restart backup',
                  baseline='10 deg/s geometry retained; 5 deg/s geometry only; fixed VOF not angular-rate coupled',
                  git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                  files=records)
    payload=json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf-8')
    identity=hashlib.sha256(payload).hexdigest()[:12]
    target=OUT/f'EVF001-source-evidence-{identity}.zip'
    if not target.exists():
        with zipfile.ZipFile(target,'x',zipfile.ZIP_DEFLATED) as z:
            for p,r in zip(selected,records): z.write(p,r['path'])
            z.writestr('ARCHIVE_MANIFEST.json',payload)
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        for r in records: assert hashlib.sha256(z.read(r['path'])).hexdigest()==r['sha256']
    (OUT/'ARCHIVE_MANIFEST.json').write_bytes(payload)
    print(json.dumps(dict(archive=str(target),files=len(records),source_bytes=sum(r['bytes'] for r in records),
                         zip_bytes=target.stat().st_size,verification='all SHA256 entries and ZIP CRC passed'),indent=2))

if __name__=='__main__': main()
