❯ I would like to have a publicly available demo hosted on a low/free cost host that anyone can access to poke around at the NexusLIMS frontend and experiement with it. I have a few requirements:

  1. Nothing about the changes required to the codebase to allow for a public demo should negatively impact the actual deployed code in real deployments
  2. The instance should give the public people django admin access so they can see what features are availble on that side. This is somewhat risky by design, so the instance should be rebooted to a fresh
  state regularly (once every 2 hours maybe? I'm not sure what's correct here) -- I'm interested in any thoughts you have on if this is a bad idea or ways to mitigate potential risks. Other open source apps
  do something similar, such as https://demo.elabftw.net/ and https://nemo-demo.atlantislabs.io/
  3. The app should either come pre-logged in as an admin user, or present a simple way to login as an admin with a button or something (this needs to be flagged behind a setting such as IS_PUBLIC_DEMO or
  something similar)
  4. The homepage text should be very focused on explaining what the app does, some of it's features, and a prominent CTA to datasophos services.
  5. We are going to need more realistic example data records built in. I'm thinking 30ish records spread across 6 different instruments is a good number. These records are going to need realistic preview
  files to feel realistic. The actual data files can maybe all be zero or one-byte placeholders so the download features work, but so our server does not get hammered in bandwidth.
    5.1. The records should come from a few different users and span different types of data acquisition, using file types across the range of supported extractors in ../NexusLIMS
    5.2. The "download files" modal should show a warning in the demo mode that it does not include real data files
  6. The demo mode should be able to be spun up easily locally using docker, and deployed on a public facing cloud server.
  7. The "initialization"/"seed" step should follow the same general process as /Users/josh/git_repos/datasophos/NexusLIMS-CDCS/deployment/docker-entrypoint.dev.sh, which runs custom initialization code as
  necessary to set things up.
    7.1. the initialization should create a few regular users as well as an admin user. The admin user will have all rights, but the two regular users should be one who is read-only (this is typical) and
  then a "project lead" type account that has write access to the records.

  If anything is unclear, please ask me about implementation details rather than guessing