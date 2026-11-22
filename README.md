# Quantum Period Finding against Symmetric Primitives in Practice (Elephant AEAD)

An academic research implementation and cryptanalytic evaluation based on:
> **"Quantum Period Finding against Symmetric Primitives in Practice"**  
> *Xavier Bonnetain and Samuel Jaques*  
> IACR Cryptology ePrint Archive Report 2020/1418 (published in *IACR Transactions on Cryptographic Hardware and Embedded Systems*, TCHES 2022).

---

## 1. Project Overview

This project investigates the post-quantum security of the NIST Lightweight Cryptography finalist **Elephant** (specifically the **Dumbo** instance). It implements the complete offline and online Simon's period-finding attack framework, evaluates the Even-Mansour reduction, and benchmarks quantum resource requirements against exhaustive key search.

### Central Research Finding
In contrast to symmetric primitives like **PRINCE** (64-bit state) and **Chaskey** (128-bit state)—which are vulnerable to offline Simon attacks requiring $\approx 2^{65}$ quantum operations—**Elephant-Dumbo** is structurally resistant. Because its state size ($n = 160$ bits) exceeds its key size ($k = 128$ bits), an offline Simon attack requires $> 2^{78}$ quantum operations and $> 1{,}600$ logical qubits. **Consequently, quantum period finding against Elephant is strictly more expensive than a Grover exhaustive key search ($2^{64}$ operations).**

---

## 2. Three-Tier Architectural Structure

```
+--------------------------------------------------------------------------------------------------+
|                                    PROJECT ARCHITECTURE                                          |
+--------------------------------------------------------------------------------------------------+
|                                                                                                  |
|  [TIER 1: FULL-SCALE SPECIFICATION] (Classical Python)                                           |
|    - Spongent-pi[160] permutation (80 rounds, 40 4-bit S-boxes, linear pLayer, 7-bit lCounter)  |
|    - LFSR mask progression phi and exact closed-form inverse phi^-1                              |
|    - Elephant-Dumbo Authenticated Encryption with Associated Data (AEAD)                         |
|    - 100% conformance with official NIST Known Answer Tests (KAT)                                |
|                                                                                                  |
|  [TIER 2: SCALED QUANTUM EXPERIMENTS] (Qiskit & Qiskit Aer)                                      |
|    - Parameterized reduced Elephant models (4-bit and 8-bit state)                              |
|    - Synthesis of exact reversible quantum oracle U_f for f(x) = E_k(x) ^ P(x)                   |
|    - Qiskit Aer simulation: Hadamard superposition -> Oracle -> Hadamard -> Measurement          |
|    - Linear system resolution over GF(2) via Gaussian elimination                                |
|    - Automatic verification: Recovered period s == Active mask, phi^-i(s) == Root mask           |
|                                                                                                  |
|  [TIER 3: THEORETICAL COMPLEXITY ANALYSIS] (Bonnetain & Jaques 2020/1418)                        |
|    - Exact analytical cost modeling for 160-bit full Dumbo                                       |
|    - Comparative analysis: Classical Brute-Force vs. Grover Key Search vs. Offline Simon         |
|    - Comparison against PRINCE and Chaskey benchmarks                                            |
|    - Automated publication-quality plots and CSV data generation                                 |
|                                                                                                  |
+--------------------------------------------------------------------------------------------------+
```

---

## 3. Directory Layout

```
Quantum_Period_Finding/
├── elephant/
│   ├── __init__.py
│   ├── spongent.py            # Spongent-pi[160] (80 rounds) permutation & S-box
│   ├── lfsr.py                # Dumbo LFSR feedback & mask derivation
│   ├── dumbo.py               # Elephant-Dumbo encrypt, decrypt, and tag generation
│   └── test_vectors.py        # Official NIST Known Answer Test (KAT) parser
├── quantum/
│   ├── __init__.py
│   ├── gf2_solver.py          # GF(2) Gaussian elimination & nullspace solver
│   ├── oracle.py              # Canonical & custom reversible Simon oracles
│   └── simon.py               # Complete Qiskit Simon algorithm runner
├── attack/
│   ├── __init__.py
│   ├── reduced_elephant.py    # Reduced-scale Even-Mansour Elephant models (4/8-bit)
│   ├── attack_oracle.py       # Quantum oracle for f(x) = E_k(x) ^ P(x)
│   └── recovery_pipeline.py   # Full attack pipeline: Circuit -> Aer -> GF(2) -> Inversion
├── experiments/
│   ├── __init__.py
│   ├── cost_analysis.py       # Bonnetain & Jaques theoretical formulas
│   └── run_experiment.py      # Master benchmark runner (Tiers 1, 2, and 3)
├── results/
│   ├── circuits/              # Saved quantum circuit diagrams
│   ├── histograms/            # Measurement distribution histograms
│   └── plots/                 # Complexity comparison graphs
├── tests/
│   ├── test_elephant.py       # Elephant encryption, decryption, and KAT tests
│   ├── test_gf2.py            # GF(2) linear algebra unit tests
│   ├── test_simon.py          # Simon algorithm validation on known periods
│   └── test_attack.py         # End-to-end period recovery validation
├── docs/
│   ├── REPORT.md              # In-depth academic research report
│   └── VIVA_QUESTIONS.md      # Comprehensive Viva Q&A with answers
├── requirements.txt
└── README.md
```

---

## 4. Installation and Setup

### Prerequisites
* Python 3.9+ (Python 3.10 to 3.14 supported)
* Virtual environment (`venv`)

### Setup Instructions
```bash
# 1. Clone or navigate to the repository
cd Quantum_Period_Finding

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

Verify the installation:
```bash
python -c "import qiskit; import qiskit_aer; import numpy; import pytest; print('Environment Verified!')"
```

---

## 5. Execution Commands

### Run the Master Demonstration
Executes Tier 1 (Elephant AEAD & NIST KAT), Tier 2 (Qiskit Aer Quantum Attacks), and Tier 3 (Resource Modeling & Plots):
```bash
PYTHONPATH=. ./venv/bin/python experiments/run_experiment.py
```

### Run the Full Automated Test Suite
Runs all 30 unit and integration tests across all modules:
```bash
PYTHONPATH=. ./venv/bin/pytest tests/ -v
```

---

## 6. Experimental Results Summary

### Tier 1: Elephant-Dumbo AEAD
* **Encryption/Decryption Symmetry:** Verified across variable plaintext lengths (0 to 100 bytes).
* **Tamper Detection:** 100% detection rate (bit-flip in ciphertext, tag, nonce, or associated data causes immediate authentication failure).
* **NIST KAT Conformance:** 100% pass on all test vectors.

### Tier 2: Quantum Period Finding (Qiskit Aer)
| Model | State Bits ($n$) | Target Active Mask | Circuit Depth | Qubits | Samples Used | Recovered Mask | Inverted Root Mask | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Reduced-4bit** | 4 | `0b1100` (12) | 70 | 8 | 5 | `0b1100` | `0b1011` | **SUCCESS** |
| **Reduced-8bit** | 8 | `0b01011001` (89) | 1,658 | 16 | 64 | `0b01011001` | `0b10101100` | **SUCCESS** |

### Tier 3: Complexity & Resource Comparison (Bonnetain & Jaques)
| Primitive | State ($n$) | Key ($k$) | Classical Brute Force | Grover Key Search | Simon Classical Queries | Simon Quantum Ops | Paper Conclusion |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Elephant-Dumbo** | **160** | **128** | $2^{128}$ | **$2^{74.9}$ gates** | $2^{53.3}$ | **$2^{78.5}$ ops** | **More expensive than Grover** |
| **Chaskey** | 128 | 128 | $2^{128}$ | $2^{74.9}$ gates | $2^{42.7}$ | $2^{65.2}$ ops | Faster than exhaustive search |
| **PRINCE** | 64 | 128 | $2^{128}$ | $2^{74.9}$ gates | $2^{21.3}$ | $2^{64.8}$ ops | Significantly faster |

---

## 7. Key Documentation Links

* Detailed Academic Report: [docs/REPORT.md](file:///Users/abhishek/Downloads/M.Tech/QC%20Project/docs/REPORT.md)
* Viva Voce Questions & Answers: [docs/VIVA_QUESTIONS.md](file:///Users/abhishek/Downloads/M.Tech/QC%20Project/docs/VIVA_QUESTIONS.md)
* Quantum Circuit Diagram: [results/circuits/simon_circuit.txt](file:///Users/abhishek/Downloads/M.Tech/QC%20Project/results/circuits/simon_circuit.txt)
* Benchmark CSV Summary: [results/attack_benchmark_summary.csv](file:///Users/abhishek/Downloads/M.Tech/QC%20Project/results/attack_benchmark_summary.csv)
* Complexity CSV Data: [results/complexity_comparison.csv](file:///Users/abhishek/Downloads/M.Tech/QC%20Project/results/complexity_comparison.csv)
