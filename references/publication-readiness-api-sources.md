# Publication Readiness API Sources

Verified 2026-08-19 against provider documentation. These sources define the deterministic reference/journal-readiness integrations. Re-verify if provider behavior changes.

## Crossref REST API

Official documentation:

- https://www.crossref.org/documentation/retrieve-metadata/rest-api/
- https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/

Implementation:

- base: `https://api.crossref.org`
- DOI metadata: `GET /works/{doi}`
- journal works: `GET /journals/{issn}/works`
- polite identification: optional `mailto` parameter / agent header

Use: primary DOI bibliographic identity and recent published/online journal records. Do not interpret Crossref presence as proof that a paper supports a manuscript claim.

## Semantic Scholar Academic Graph API

Official documentation:

- https://www.semanticscholar.org/product/api
- https://www.semanticscholar.org/product/api/tutorial
- https://api.semanticscholar.org/api-docs/

Implementation:

- base: `https://api.semanticscholar.org/graph/v1`
- paper details: `GET /paper/{paper_id}`
- DOI identifier format: `DOI:<doi>`
- search: `GET /paper/search`
- optional/recommended API key header: `x-api-key`

Use: independent bibliographic corroboration, abstracts/citation metadata when returned, and advisory similar-paper discovery. The similarity precheck is not a licensed plagiarism checker.

## NCBI PubMed E-utilities

Official documentation:

- https://www.ncbi.nlm.nih.gov/home/develop/api/
- https://www.ncbi.nlm.nih.gov/books/NBK25499/

Implementation:

- base: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils`
- DOI search in PubMed: ESearch with `db=pubmed` and DOI query
- metadata summary: ESummary for returned PMID
- optional API key: `api_key`

Use: biomedical reference corroboration when the DOI is indexed in PubMed. Absence from PubMed is not evidence that a non-biomedical reference is invalid.

## Source hierarchy

For final decisions:

1. journal/publisher official page for scope, article type, templates, policies and submission requirements;
2. Crossref / NCBI / Semantic Scholar for bibliographic/recent-literature metadata;
3. local seed configuration only as fallback/discovery, never as current final authority.

Every runtime retrieval should record retrieval time and provider. Network errors are `unknown/unverified`, never PASS.
