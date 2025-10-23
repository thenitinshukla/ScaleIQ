# CINECA HPC Software Documentation

## Overview

CINECA HPC clusters provide a large set of pre-installed software packages accessible through the **module** system.  
Users can view, load, and manage software environments via the `module` and `modmap` commands.

For a complete and updated list of available applications and versions, please consult the  
[**CINECA Software Catalog**](https://www.hpc.cineca.it/systems/software/).

It is also possible to install software independently, using available compilers or the **Spack** package manager.

Some applications are freely available, while others require a valid license.  
CINECA provides centralized licenses for several commercial packages, but in some cases user authorization is required.  
For other licensed software not covered by CINECA, users may configure access to their own license server.

---

## Software Available with CINECA License

The following software packages are provided under CINECA-managed licenses and can be used directly via the module system.  
No additional steps are needed — users simply load the appropriate module.

| Software | Notes |
|-----------|-------|
| **Amber24** | Molecular dynamics suite for biomolecular simulations. |
| **AMS** | Amsterdam Modeling Suite for computational chemistry. |
| **IDL** | Interactive Data Language for data analysis and visualization. |
| **Molcas** | Quantum chemistry software for multiconfigurational calculations. |
| **Molpro** | Quantum chemistry suite for ab initio simulations. |
| **Q-Chem** | Ab initio quantum chemistry package. |
| **Totalview** | Parallel debugger and performance analysis tool for HPC codes. |

---

## Software Available Using Your Own License

For certain commercial applications, users must use their own valid licenses.  
Below are the steps and policies for these software packages.

### Gaussian

- CINECA provides its own license for Gaussian.
- To gain access, users must email **superc@cineca.it** requesting authorization to load the module.

### VASP

- CINECA **does not** provide licenses for VASP.
- Users must use their own license or be part of a research group holding a valid VASP license.
- Send an email to **superc@cineca.it**, specifying:
  - That you or your institution possess a VASP license
  - The **software version** requested
  - The **license holder’s name** and **registered email** (if part of a research group)
- After verification with VASP developers, you will be granted access to the VASP module.

### MATLAB

- Through an agreement with **MathWorks**, CINECA provides MATLAB licenses via an internal license server.
- Usage is allowed **only for Open Science (non-commercial)** research activities.
- To request access:
  - Contact **superc@cineca.it**
  - Declare that your work is non-commercial and part of Open Science
- Once approved, you’ll be authorized to use MATLAB modules with CINECA’s license.

### Crystal

- CINECA does not provide Crystal licenses; users must rely on their own.
- To enable module access:
  - Email **superc@cineca.it**, specifying that you (or your supervisor) own a Crystal license.
  - Include license type (e.g., *Basic* or *Basic+MPP*).
  - CC **info@crystalsolutions.eu** and the license holder.
- After verification with the Crystal developers, authorization will be granted.

---

## How to Connect Your Own License Server

If you own a **FlexLM** (FlexNet) license and wish to use it on CINECA clusters, follow this procedure:

1. Contact **superc@cineca.it** and provide:
   - **Port** and **host/IP** of the license server.
   - A signed declaration (template provided by CINECA) confirming ownership of a valid license.  
     You can download the official template here:  
     [License Declaration Template (ODT)](https://docs.hpc.cineca.it/_downloads/5f06a7444bf288186b0992dabb10a69e/License_request.odt)

2. CINECA will send you the list of IP addresses from their clusters, which your license server administrator must whitelist in the firewall.

3. After validation, your **username** and **HPC account(s)** will be authorized to run jobs using your license.

**If you use an academic license:**
- You must also provide a contact representative (who can approve new users for the same license in the future).

---

## Advanced Software-Specific Documentation

For additional information and specific configurations, CINECA provides dedicated documentation for major applications:

| Software | Documentation Link |
|-----------|--------------------|
| **MATLAB** | [Matlab on CINECA HPC](https://docs.hpc.cineca.it/hpc/software/matlab.html#matlab-card) |
| **Quantum ESPRESSO** | [Quantum ESPRESSO on CINECA HPC](https://docs.hpc.cineca.it/hpc/software/qe.html#quantum-espresso-card) |

---

© 2025 — CINECA HPC User Support Team  
Built with [Sphinx](https://www.sphinx-doc.org/) using the [Read the Docs theme](https://github.com/readthedocs/sphinx_rtd_theme).
