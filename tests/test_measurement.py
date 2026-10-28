import csv
import json
from pathlib import Path
import dns.edns
import dns.message
import dns.rcode
import dns.rrset
import pytest

from pdns_lab.analysis import agreement, analyze
from pdns_lab.cli import main, context_snapshot
from pdns_lab.corpus import build_legacy, read_corpus, write_corpus, normalize_domain, FIELDS, LEGACY
from pdns_lab.dnsprobe import classify, summarize_response, probe
from pdns_lab.storage import Store
from pdns_lab.ooni import export_urls, import_measurements
from pdns_lab.http_probe import probe_http


def response(rcode="NOERROR", addresses=(), ede=(), error=None):
    return {"rcode": rcode, "addresses": list(addresses), "ede": list(ede), "error": error}


def test_nxdomain_is_not_automatic_block():
    negative = response("NXDOMAIN")
    positive = response(addresses=["93.184.216.34"])
    assert classify(negative, negative, negative, {})[0] == "indeterminado"
    assert classify(negative, positive, positive, {})[0] == "anomalia"
    assert classify(negative, positive, response(error="Timeout"), {})[0] == "indeterminado"


def test_policy_signals_and_transport_errors_are_distinct():
    assert classify(response("REFUSED"), None, None, {})[0] == "indeterminado"
    assert classify(response(error="Timeout"), None, None, {})[0] == "error_red"
    assert classify(response("NXDOMAIN", ede=[{"code": 15}]), None, None, {})[0] == "bloqueo_senalizado"
    assert classify(response("SERVFAIL", ede=[{"code": 6}]), None, None, {})[0] == "indeterminado"


def test_sinkhole_requires_documented_fingerprint():
    target = response(addresses=["0.0.0.0"])
    assert classify(target, None, None, {})[0] == "anomalia"
    assert classify(target, None, None, {"fingerprint_ips": ["0.0.0.0"]})[0] == "anomalia"
    assert classify(target, None, None, {"fingerprint_ips": ["0.0.0.0"], "fingerprint_source": "official"})[0] == "bloqueo_senalizado"


def test_different_cdn_addresses_do_not_imply_block():
    a, b = response(addresses=["93.184.216.34"]), response(addresses=["93.184.216.35"])
    assert classify(a, b, b, {})[0] == "resolucion_observada"


def test_wire_preserves_multiple_answers_and_ttl():
    query = dns.message.make_query("example.com", "A")
    reply = dns.message.make_response(query)
    reply.answer.append(dns.rrset.from_text("example.com.", 123, "IN", "A", "192.0.2.1", "192.0.2.2"))
    reply.use_edns(options=[dns.edns.EDEOption(15, "policy")])
    data = summarize_response(reply)
    assert data["addresses"] == ["192.0.2.1", "192.0.2.2"]
    assert data["answer"][0]["ttl"] == 123
    assert data["ede"][0]["code"] == 15
    assert data["wire_base64"]


def test_retries_are_preserved(monkeypatch):
    calls = []
    def fake(query, endpoint, **kwargs):
        calls.append(endpoint)
        if len(calls) == 1:
            raise OSError("network down")
        return dns.message.make_response(query), True
    monkeypatch.setattr("pdns_lab.dnsprobe.dns.query.udp_with_fallback", fake)
    result = probe("example.com", "A", "192.0.2.1", retries=1, interval=0)
    assert len(result["attempts"]) == 2
    assert result["attempts"][0]["error"] == "OSError"
    assert result["final"]["transport"] == "tcp"


@pytest.mark.parametrize("value", ["https://example.com/a", "127.0.0.1", "::1", "bad name.com", "localhost", "-bad.example"])
def test_invalid_domains_are_rejected(value):
    with pytest.raises(ValueError):
        normalize_domain(value)


def test_corpus_keeps_overlap_and_provenance(tmp_path):
    for filename in LEGACY:
        (tmp_path/filename).write_text("SHARED.example.\n")
    output = tmp_path/"corpus.csv"
    audit = build_legacy(tmp_path, output)
    rows = read_corpus(output)
    assert audit["input_rows"] == 5
    assert len(rows) == 1 and len(rows[0]["categories"].split("|")) == 5
    assert rows[0]["validation_status"] == "pending"
    assert len(json.loads(rows[0]["sources"])) == 5
    with pytest.raises(ValueError):
        build_legacy(tmp_path, output)
    with pytest.raises(ValueError):
        export_urls(rows, tmp_path/"urls.txt")


def test_kappa_degenerate_and_pairwise_counts():
    result = agreement([(0,0)]*3)
    assert result["agreement"] == 1 and result["kappa"] is None
    assert result["jaccard_block"] is None
    assert agreement([])["n"] == 0
    assert agreement([(0,0),(1,1)])["kappa"] == 1


def test_pairwise_missingness_does_not_require_third_profile(tmp_path):
    db = tmp_path/"test.sqlite3"
    store = Store(db)
    store.start("r", "now", {"rounds": 2, "expected_samples": 6})
    row = {"domain":"example.com", "categories":"popular|adultos", "validation_status":"pending"}
    for p in ["a", "b", "c"]:
        for round_number in [1,2]:
            status = "error_red" if p == "c" else "resolucion_observada"
            store.save("r", row, p, "A", round_number, status, "test", {})
    store.close()
    result = analyze(db, "r")
    ab = next(p for p in result["pairwise"] if p["a"] == "a" and p["b"] == "b" and p["category"] == "ALL")
    assert ab["n"] == 1 and ab["excluded_domains"] == 0
    assert result["complete"] is True


def test_unstable_or_incomplete_rounds_are_excluded(tmp_path):
    db = tmp_path/"test.sqlite3"
    store = Store(db)
    store.start("r", "now", {"rounds": 2, "expected_samples": 4})
    row = {"domain":"example.com", "categories":"popular", "validation_status":"validated"}
    store.save("r", row, "a", "A", 1, "bloqueo_senalizado", "test", {})
    store.save("r", row, "a", "A", 2, "resolucion_observada", "test", {})
    store.save("r", row, "b", "A", 1, "resolucion_observada", "test", {})
    store.close()
    result = analyze(db, "r")
    assert result["complete"] is False
    assert all(p["n"] == 0 for p in result["pairwise"])


def test_ooni_blocking_false_is_not_a_truthy_label(tmp_path):
    source = tmp_path/"ooni.jsonl"
    source.write_text(json.dumps({"test_name":"web_connectivity", "input":"https://example.com/", "test_keys":{"blocking":False,"accessible":True}})+"\n")
    rows = import_measurements(source)
    assert rows[0]["blocking"] is False and rows[0]["accessible"] is True


def test_full_offline_run_records_control_and_target(monkeypatch, tmp_path):
    corpus = tmp_path/"corpus.csv"
    row = dict.fromkeys(FIELDS, "")
    row.update(domain="example.com", categories="popular", sources="test", validation_status="pending")
    write_corpus(corpus,[row])
    profiles = tmp_path/"profiles.json"
    profiles.write_text(json.dumps({"profiles":[{"id":"p","kind":"dns","enabled":True,"endpoint":"192.0.2.1","reference":"192.0.2.2"}]}))
    calls = []
    def fake(domain,qtype,endpoint,**kwargs):
        calls.append(endpoint)
        final = response(addresses=["192.0.2.3"])
        return {"attempts":[final],"final":final}
    monkeypatch.setattr("pdns_lab.cli.probe",fake)
    db=tmp_path/"new.sqlite3"
    main(["run","--corpus",str(corpus),"--profiles",str(profiles),"--db",str(db),"--rounds","2","--qtypes","A","--include-unreviewed"])
    import sqlite3
    con=sqlite3.connect(db)
    run_id, metadata = con.execute("SELECT run_id,metadata_json FROM runs").fetchone()
    assert json.loads(metadata)["exploratory"] is True
    evidence=json.loads(con.execute("SELECT evidence_json FROM samples LIMIT 1").fetchone()[0])
    assert evidence["control_before"] and evidence["control_after"] and evidence["target"]
    assert len(calls)==6
    assert analyze(db,run_id)["complete"] is True


def test_http_403_does_not_become_a_confirmed_block(monkeypatch):
    import httpx
    transport = httpx.MockTransport(lambda request: httpx.Response(403, text="Forbidden"))
    original = httpx.Client
    monkeypatch.setattr("pdns_lab.http_probe.httpx.Client",lambda **kwargs: original(transport=transport,**kwargs))
    result=probe_http("https://example.com")
    assert result["http_status"] == 403
    assert result["status"] == "respuesta_http_observada"


def test_vpn_requires_a_real_context(tmp_path):
    profiles=[{"kind":"vpn","endpoint":"192.0.2.1"}]
    with pytest.raises(ValueError):
        context_snapshot(None,profiles)
    context=tmp_path/"context.json"
    context.write_text(json.dumps({"kind":"vpn","interface":"tun0","filter_setting":"REEMPLAZAR"}))
    with pytest.raises(ValueError):
        context_snapshot(context,profiles)


def test_http_fingerprint_preserves_source_and_redacts_proxy_credentials(monkeypatch):
    import httpx
    original=httpx.Client
    transport=httpx.MockTransport(lambda request: httpx.Response(200,text="A documented block page"))
    def client(**kwargs):
        kwargs.pop("proxy",None)
        return original(transport=transport,**kwargs)
    monkeypatch.setattr("pdns_lab.http_probe.httpx.Client",client)
    result=probe_http("https://example.com",proxy="http://user:secret@127.0.0.1:8080",fingerprints=[{"text":"documented block page","source":"calibration evidence"}])
    assert result["status"] == "bloqueo_senalizado"
    assert result["matched_fingerprints"][0]["source"] == "calibration evidence"
    assert "secret" not in json.dumps(result) and "user:" not in json.dumps(result)


def test_study_separates_target_candidates_and_validated(tmp_path):
    from pdns_lab.study import plan_study, select_study
    study = tmp_path/'study.json'
    study.write_text(json.dumps({'id':'parental','target_unique_domains':2,'target_origin':'test',
                                 'seed':42,'included_categories':['adultos','educativo'],
                                 'excluded_categories':['phishing']}))
    rows = [{'domain':f'site{i}.example','categories':c,'sources':'[]',
             'validation_status':'pending','validation_evidence':'','reviewer':'','reviewed_at':''}
            for i,c in enumerate(['adultos','phishing','adultos|phishing','educativo'])]
    corpus=tmp_path/'corpus.csv'
    write_corpus(corpus,rows)
    plan=plan_study(corpus,study)
    assert plan['input_domains']==4 and plan['in_scope_candidates']==3
    assert plan['in_scope_validated']==0 and plan['validation_gap']==2
    with pytest.raises(ValueError,match='disponibles: 0'):
        select_study(corpus,study,tmp_path/'final.csv')
    assert not (tmp_path/'final.csv').exists()
    for row in rows:
        row.update(validation_status='validated',validation_evidence='documented category',reviewer='Reviewer',reviewed_at='2026-10-27')
    write_corpus(corpus,rows)
    one,two=tmp_path/'one.csv',tmp_path/'two.csv'
    select_study(corpus,study,one)
    select_study(corpus,study,two)
    assert one.read_bytes()==two.read_bytes()
    chosen=read_corpus(one)
    assert len(chosen)==2 and len({r['domain'] for r in chosen})==2
    assert all('phishing' not in r['categories'] for r in chosen)
    with pytest.raises(ValueError,match='ya existe'):
        select_study(corpus,study,one)


def test_study_selection_produces_exactly_2000_without_duplicates(tmp_path):
    from pdns_lab.study import select_study
    study=tmp_path/'study.json'
    study.write_text(json.dumps({'id':'parental','target_unique_domains':2000,'target_origin':'test',
                                 'seed':42,'included_categories':['educativo'],'excluded_categories':['phishing']}))
    corpus=tmp_path/'corpus.csv'
    write_corpus(corpus,[{'domain':f'site{i}.example','categories':'educativo','sources':'[]',
                         'validation_status':'validated','validation_evidence':'test-only evidence',
                         'reviewer':'test reviewer','reviewed_at':'2026-10-27'} for i in range(2010)])
    result=select_study(corpus,study,tmp_path/'final.csv')
    assert result['selected_domains']==2000 and result['selected_memberships']['educativo']==2000
    assert len(read_corpus(tmp_path/'final.csv'))==2000


def test_parental_candidates_preserve_provenance_and_do_not_validate(tmp_path):
    from pdns_lab.study import build_parental_candidates
    study=tmp_path/'study.json'
    study.write_text(json.dumps({'id':'parental','target_unique_domains':4,'target_origin':'test',
                                 'seed':42,'included_categories':['adultos','referencia_biblioteca'],
                                 'excluded_categories':['phishing']}))
    corpus=tmp_path/'in.csv'
    write_corpus(corpus,[{'domain':f'site{i}.example','categories':category,'sources':'[]',
                         'validation_status':'pending','validation_evidence':'','reviewer':'','reviewed_at':''}
                        for i,category in enumerate(['adultos','phishing'])])
    source=tmp_path/'source.txt'
    source.write_text('127.0.0.1\nsite0.example\nref1.example\nref1.example\nref2.example\n')
    with pytest.raises(ValueError,match='sin duplicados'):
        build_parental_candidates(corpus,study,source,tmp_path/'out.csv')
    assert not (tmp_path/'out.csv').exists()
    source.write_text(source.read_text()+'ref3.example\n')
    result=build_parental_candidates(corpus,study,source,tmp_path/'out.csv')
    rows=read_corpus(tmp_path/'out.csv')
    assert len(rows)==4 and result['added_reference_candidates']==3
    assert all(r['categories']!='phishing' and r['validation_status']=='pending' for r in rows)
    for row in rows:
        if row['categories']=='referencia_biblioteca':
            provenance=json.loads(row['sources'])[0]
            assert source.read_text().splitlines()[provenance['line']-1]==row['domain']
            assert provenance['sha256']==result['reference_source_sha256']
