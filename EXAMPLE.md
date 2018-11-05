# JSON Examples
-----
As part of my repo, I've included some examples of both the streaming API and the full API.  I've redacted some aspects as they are very particular to me, and wanted to ensure I maintain some privacy. 

In the examples (tesla_full_example.json and tesla_stream_example.json) if you see type_redact I've remove that data. 

There are three type_redact, str_redact, int_redact, and flt_redact to indicate what the type was before I redacted it.  If you try to parse this JSON you will get errors unless you put in an INT or a FLOAT for int_redact and flt_redact

Also of note: it looks like the streaming API uses all strings, while the full uses real types. Be aware of this
