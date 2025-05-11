
Personal Project
================

Tools
-----

`Davinci Resolve <https://www.blackmagicdesign.com/products/davinciresolve>`_
   Editing and compositing video
`FFmpeg <https://ffmpeg.org/>`_
   Media conversion, used with `yt-dlp`
`OBS Studio <https://obsproject.com/>`_
   Desktop recording
`yt-dlp <https://github.com/yt-dlp/yt-dlp>`_
   Downloading media

Downloads
---------

- :download:`Davinci Resolve: Video Templates (Project Reality) <../../_downloads/Video Templates (Project Reality).drp>`

Useful Commands
---------------

yt-dlp
^^^^^^

.. describe:: yt-dlp -f bv+ba <link path>

   Downloads the best video and audio from a link.

.. describe:: yt-dlp -f bv+ba -a <.txt file path>

   Downloads the best video and audio from a list.

.. describe:: yt-dlp -f bestaudio[ext=m4a]+bestvideo[ext=mp4] --merge-output-format mkv --sleep-interval 10 --max-sleep-interval 30 -r 8m -4 --sleep-requests 2 --sleep-interval 5

   Downloads in mp4+m4a video format. Restrict download rate and sleep the requests to prevent restrictions.
