# Sample logs

These are **synthetic** logs designed to exercise the analyzer end-to-end. No real victims, no real IOCs — IPs and hashes are made up.

| File | Scenario | Expected MITRE techniques |
|------|----------|---------------------------|
| `apt_phishing_to_ransomware.log` | Macro-laced invoice → PowerShell loader → credential dump → lateral move via PsExec → ransomware | T1566.001, T1059.001, T1547.001, T1003, T1021.002, T1486, T1490 |
| `web_exploit_to_rce.log`         | Brute-forced WP login → malicious plugin upload → web shell → reverse shell on host | T1110, T1190, T1505.003, T1059.004, T1071.001 |
| `insider_data_exfil.log`         | Departing employee accessing restricted files → cloud upload + USB exfil | T1078.002, T1530, T1052.001, T1567.002 |

Drop them into the Streamlit UI or run from the CLI:

```bash
neural-architect analyze data/samples/apt_phishing_to_ransomware.log
```
