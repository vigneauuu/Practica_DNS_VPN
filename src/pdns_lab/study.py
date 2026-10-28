"""Plan y selección del corpus final, separados de las listas candidatas."""
import json
import random
from pathlib import Path

from .corpus import CATEGORIES, read_corpus, sha256, write_corpus


def load_study(path):
    study = json.loads(Path(path).read_text(encoding="utf-8"))
    target = study.get("target_unique_domains")
    if isinstance(target, bool) or not isinstance(target, int) or target < 1:
        raise ValueError("La meta debe ser un entero positivo")
    included = set(study.get("included_categories", []))
    excluded = set(study.get("excluded_categories", []))
    if not included or not (included | excluded) <= CATEGORIES or included & excluded:
        raise ValueError("Categorías de alcance inválidas")
    return study


def eligible_rows(rows, study, *, validated=False):
    included = set(study["included_categories"])
    excluded = set(study.get("excluded_categories", []))
    result = []
    for row in rows:
        labels = set(row["categories"].split("|"))
        # Una etiqueta fuera del alcance no elimina una etiqueta parental documentada.
        scoped = labels & included - excluded
        if not scoped or row["validation_status"] == "excluded":
            continue
        if validated and row["validation_status"] != "validated":
            continue
        result.append({**row, "categories": "|".join(sorted(scoped))})
    return result


def plan_study(corpus, study_path):
    study = load_study(study_path)
    rows = read_corpus(corpus)
    candidates = eligible_rows(rows, study)
    reviewed = eligible_rows(rows, study, validated=True)
    target = study["target_unique_domains"]
    return {"study": study["id"], "target_unique_domains": target,
            "target_origin": study["target_origin"], "input_domains": len(rows),
            "in_scope_candidates": len(candidates), "in_scope_validated": len(reviewed),
            "additional_candidates_needed": max(0, target-len(candidates)),
            "validation_gap": max(0, target-len(reviewed)),
            "ready_for_selection": len(reviewed) >= target,
            "candidate_memberships": {c: sum(c in r["categories"].split("|") for r in candidates)
                                      for c in study["included_categories"]},
            "excluded_categories": study.get("excluded_categories", []),
            "corpus_sha256": sha256(corpus), "study_sha256": sha256(study_path),
            "note": "La meta no acredita datos obtenidos, balance de categorías ni representatividad estadística."}


def select_study(corpus, study_path, output):
    output = Path(output)
    if output.exists() or output.with_suffix(".selection.json").exists():
        raise ValueError("La salida ya existe; conserve el historial de selección")
    study = load_study(study_path)
    rows = sorted(eligible_rows(read_corpus(corpus), study, validated=True), key=lambda r: r["domain"])
    target = study["target_unique_domains"]
    if len(rows) < target:
        raise ValueError(f"Se requieren {target} dominios validados en alcance; disponibles: {len(rows)}")
    random.Random(study["seed"]).shuffle(rows)
    selected = sorted(rows[:target], key=lambda r: r["domain"])
    write_corpus(output, selected)
    manifest = {**plan_study(corpus, study_path), "selected_domains": len(selected),
                "seed": study["seed"], "selection": "Sin reemplazo entre dominios validados en alcance; sin cuotas por categoría",
                "selected_corpus_sha256": sha256(output),
                "selected_memberships": {c: sum(c in r["categories"].split("|") for r in selected)
                                         for c in study["included_categories"]}}
    output.with_suffix(".selection.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return manifest


def build_parental_candidates(corpus, study_path, reference_source, output):
    """Completa el conjunto candidato con contraste universitario, sin validar etiquetas."""
    from .corpus import normalize_domain
    output = Path(output)
    if output.exists() or output.with_suffix('.build.json').exists():
        raise ValueError('La salida ya existe; conserve el historial')
    study = load_study(study_path)
    rows = eligible_rows(read_corpus(corpus), study)
    target = study['target_unique_domains']
    needed = target-len(rows)
    if needed and 'referencia_biblioteca' not in study['included_categories']:
        raise ValueError('La categoría de contraste no está incluida en el estudio')
    if needed < 0:
        raise ValueError('El inventario en alcance excede la meta; no se trunca implícitamente')
    existing = {r['domain'] for r in rows}
    pool, rejected = {}, []
    for line, value in enumerate(Path(reference_source).read_text(encoding='utf-8').splitlines(),1):
        try:
            domain = normalize_domain(value)
        except ValueError as exc:
            rejected.append({'line':line,'reason':str(exc)})
            continue
        if domain not in existing:
            pool.setdefault(domain,line)
    if len(pool) < needed:
        raise ValueError('La fuente de contraste no permite completar la meta sin duplicados')
    chosen = random.Random(study['seed']).sample(sorted(pool),needed)
    digest = sha256(reference_source)
    for domain in chosen:
        provenance = {'file':Path(reference_source).name,'line':pool[domain],'sha256':digest,
                      'url':'https://dsi.ut-capitole.fr/blacklists/download/liste_bu.tar.gz',
                      'description':'UT1 liste_bu: referencia universitaria; no acredita por sí sola contenido educativo ni benignidad'}
        rows.append({'domain':domain,'categories':'referencia_biblioteca',
                     'sources':json.dumps([provenance],ensure_ascii=False,sort_keys=True),
                     'validation_status':'pending','validation_evidence':'','reviewer':'','reviewed_at':''})
    rows.sort(key=lambda r:r['domain'])
    write_corpus(output,rows)
    manifest = {'input_sha256':sha256(corpus),'study_sha256':sha256(study_path),
                'reference_source_sha256':digest,'source_url':'https://dsi.ut-capitole.fr/blacklists/download/liste_bu.tar.gz',
                'source_description_url':'https://dsi.ut-capitole.fr/blacklists/',
                'seed':study['seed'],'inherited_in_scope':target-needed,'added_reference_candidates':needed,
                'reference_available_nonoverlapping':len(pool),'rejected_reference_lines':rejected,
                'unique_candidates':len(rows),'candidate_corpus_sha256':sha256(output),
                'validation':'No se valida automáticamente ninguna entrada nueva; se conserva la revisión de las heredadas'}
    output.with_suffix('.build.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return manifest
