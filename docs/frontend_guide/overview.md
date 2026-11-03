(cdcs-overview)=
# Overview

NexusLIMS CDCS is the web frontend for NexusLIMS. It stores experimental records
built by the NexusLIMS backend and lets people find, view, and curate them.

It builds on the open-source [Configurable Data Curation System](https://cdcs.nist.gov/)
developed by NIST. NexusLIMS CDCS is maintained by [Datasophos](https://datasophos.co)
and is not affiliated with NIST.

## Explore the frontend

- {doc}`Finding records <search>` covers browsing and keyword search.
- {doc}`Viewing records and data <record-details>` explains record
  details, samples, datasets, and file downloads.
- {doc}`Annotating and curating records <record-curation>` covers descriptions,
  ratings, featured datasets, and the record editor.
- {doc}`Public dataset gallery <public-gallery>` explains the rotating gallery
  and how administrators choose eligible images.
- {doc}`Screenshot gallery <gallery>` provides a visual tour of the interface.

## Deployment and compatibility

To run CDCS, start with the {doc}`production deployment <production>` or
{doc}`development setup <development>` guide. When upgrading, check the
[NexusLIMS compatibility matrix](https://datasophos.github.io/NexusLIMS/stable/reference/compatibility.html)
to choose a frontend version compatible with your backend.

```{toctree}
:hidden:

Screenshot gallery <gallery>
Finding records <search>
Viewing records and data <record-details>
Annotating and curating records <record-curation>
Public dataset gallery <public-gallery>
```
