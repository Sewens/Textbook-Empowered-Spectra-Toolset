import json
from pathlib import Path
from app.services.material_spectrum_claims_service import MaterialSpectrumClaimsService

def test_claim_requires_direct_material_spectrum_evidence_and_cm1(tmp_path: Path):
    release=tmp_path/'evidence'; release.mkdir()
    (release/'evidence_links.json').write_text(json.dumps({'items':[
      {'evidence_id':'EV1','material_id':'MAT_ETHANOL','material_name':'ethanol','spectrum_id':'SPEC1','book':'Book','source_id':'SRC','page':8,'support_strength':'high','evidence_type':'paragraph','text':'The infrared spectrum of ethanol shows an O-H band at 3342 cm-1 and a C-C-O band at 1050 cm-1.'},
      {'evidence_id':'EV2','material_id':'MAT_ETHANOL','material_name':'ethanol','spectrum_id':'SPEC2','book':'Book','text':'A spectrum has a band at 3342 cm-1.'},
      {'evidence_id':'EV3','material_id':'MAT_ACETONE','material_name':'acetone','spectrum_id':'SPEC3','book':'Book','text':'acetone is discussed in Figure 7 without wavenumber.'},
    ]}),encoding='utf-8')
    claims=MaterialSpectrumClaimsService.build_claims(release)
    assert len(claims)==1
    claim=claims[0]
    assert claim['material_id']=='MAT_ETHANOL'
    assert claim['spectrum_id']=='SPEC1'
    assert claim['evidence_ids']==['EV1']
    assert claim['predicate']=='has_observed_band'
    assert claim['object']['frequencies_cm1'][0]['lower']==3342.0

def test_effect_needs_explicit_causal_direction(tmp_path: Path):
    release=tmp_path/'evidence'; release.mkdir()
    (release/'evidence_links.json').write_text(json.dumps({'items':[
      {'evidence_id':'EV1','material_id':'MAT_E','material_name':'ethanol','spectrum_id':'SPEC1','book':'Book','text':'In the infrared spectrum of ethanol, hydrogen bonding broadens the O-H band near 3300 cm-1.'},
      {'evidence_id':'EV2','material_id':'MAT_E','material_name':'ethanol','spectrum_id':'SPEC2','book':'Book','text':'The infrared spectrum of ethanol has a broad O-H band near 3300 cm-1.'},
    ]}),encoding='utf-8')
    claims=MaterialSpectrumClaimsService.build_claims(release)
    assert {c['predicate'] for c in claims}=={'broadened_by','has_observed_band'}
    assert all('EV' in c['evidence_ids'][0] for c in claims)


def test_rejects_material_token_embedded_in_unrelated_formula(tmp_path: Path):
    release=tmp_path/'evidence'; release.mkdir()
    (release/'evidence_links.json').write_text(json.dumps({'items':[
      {'evidence_id':'EV1','material_id':'MAT_CO','material_name':'CO','spectrum_id':'SPEC1','book':'Book','text':'The COO stretching bands of EDTA appear at 1550 cm-1.'},
      {'evidence_id':'EV2','material_id':'MAT_CO','material_name':'CO','spectrum_id':'SPEC2','book':'Book','text':'The infrared spectrum of CO exhibits a band at 2143 cm-1.'},
    ]}),encoding='utf-8')
    claims=MaterialSpectrumClaimsService.build_claims(release)
    assert len(claims)==1
    assert claims[0]['spectrum_id']=='SPEC2'


def test_rejects_short_formula_prefix_in_co2(tmp_path: Path):
    release=tmp_path/'evidence'; release.mkdir()
    (release/'evidence_links.json').write_text(json.dumps({'items':[
      {'evidence_id':'EV1','material_id':'MAT_CO','material_name':'CO','spectrum_id':'SPEC1','book':'Book','text':'The infrared spectrum of CO2 exhibits bands at 2359 cm-1.'},
    ]}),encoding='utf-8')
    assert MaterialSpectrumClaimsService.build_claims(release)==[]


def test_rejects_short_formula_with_spaced_subscript(tmp_path: Path):
    release=tmp_path/'evidence'; release.mkdir()
    (release/'evidence_links.json').write_text(json.dumps({'items':[
      {'evidence_id':'EV1','material_id':'MAT_CO','material_name':'CO','spectrum_id':'SPEC1','book':'Book','text':'The infrared spectrum of CO _3 exhibits a band at 1433 cm-1.'},
    ]}),encoding='utf-8')
    assert MaterialSpectrumClaimsService.build_claims(release)==[]


def test_keeps_only_frequency_nearest_to_named_material(tmp_path: Path):
    release=tmp_path/'evidence'; release.mkdir()
    (release/'evidence_links.json').write_text(json.dumps({'items':[
      {'evidence_id':'EV1','material_id':'MAT_CO','material_name':'CO','spectrum_id':'SPEC1','book':'Book','text':'The IR spectrum of the CO molecule is at 2136 cm-1 and that of CO2 is 2349 cm-1.'},
      {'evidence_id':'EV2','material_id':'MAT_CO','material_name':'CO','spectrum_id':'SPEC2','book':'Book','text':'The spectrum identifies CO, CO2 and HCHO. An unknown ozone band occurs at 1090-1150 cm-1.'},
    ]}),encoding='utf-8')
    claims=MaterialSpectrumClaimsService.build_claims(release)
    assert len(claims)==1
    assert claims[0]['object']['frequencies_cm1']==[{'lower':2136.0,'upper':2136.0,'raw_text':'2136 cm-1'}]
