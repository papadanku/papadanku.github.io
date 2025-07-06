
Project PAPADANKU
=================

Design
------

- Keep design *aesthetic* and *accessible*.
- Use *Plain English* if possible.
- **Feelings:** Calm, Vintage.

  An example is previous content like `realitywave <https://www.youtube.com/watch?v=QfLXRnAuV0g>`_

- **Approach:** Sans-Serif \(Geometric, Rounded\).

  CShade values uniformity, simplicity, and precision. A rounded font encourages feelings of softness and friendliness, which CShade values in its content.

.. list-table:: Fonts
  :header-rows: 1

  * - Usage
    - Font
  * - Video Text
    - `Jost Medium <https://fonts.google.com/specimen/Jost>`_
  * - Thumbnail Text
    - `Cooper* Bold <https://indestructibletype.com/Cooper/index.html>`_

Tools
-----

.. list-table::
   :header-rows: 1

   * - Software
     - Usage
   * - `Audacity <https://www.audacityteam.org/>`_
     - Editing and compositing video
   * - `Davinci Resolve <https://www.blackmagicdesign.com/products/davinciresolve>`_
     - Editing and compositing video
   * - `FFmpeg <https://ffmpeg.org/>`_
     - Media conversion, used with `yt-dlp`
   * - `OBS Studio <https://obsproject.com/>`_
     - Desktop recording
   * - `yt-dlp <https://github.com/yt-dlp/yt-dlp>`_
     - Downloading media

Useful Commands
---------------

.. list-table:: yt-dlp
   :header-rows: 1

   * - Command
     - Description
   * - ``yt-dlp -f bv+ba <link path>``
     - Downloads the best video and audio from a link.
   * - ``yt-dlp -f bv+ba -a <.txt file path>``
     - Downloads the best video and audio from a list.
   * - ``yt-dlp -f bestaudio[ext=m4a]+bestvideo[ext=mp4] --merge-output-format mkv --sleep-interval 10 --max-sleep-interval 30 -r 8m -4 --sleep-requests 2 --sleep-interval 5``
     - Downloads in mp4+m4a video format. Restrict download rate and sleep the requests to prevent restrictions.
