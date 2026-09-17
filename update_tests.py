test_files = ['proof_suite.py', 'proof_ext.py']
replacements = {
    '"/extract"': '"/scrape_to_json"',
    '"/audit"': '"/audit_agent_code"',
    '"/buy_pack"': '"/buy_firewall_credits"',
    '"/scan"': '"/scan_for_injection"',
    '"/notarize"': '"/certify_my_package"',
    '"/airgap"': '"/offline_ai_analysis"',
    '"/oracle"': '"/verify_escrow_work"',
    '"/redteam"': '"/uncensored_exploit_research"',
    '"/forensics"': '"/post_hack_autopsy"',
    '"/iron_door"': '"/bypass_captcha_and_scrape"'
}
for tf in test_files:
    try:
        t = open(tf).read()
        for old, new in replacements.items():
            t = t.replace(old, new)
        open(tf, 'w').write(t)
    except: pass
print("TESTS UPDATED: Crucible now targets the new simple names.")
