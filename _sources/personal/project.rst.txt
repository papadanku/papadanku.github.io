
Project PAPADANKU
=================

Design
------

- Keep design *aesthetic* and *accessible*.
- Use *Plain English* if possible.
- **Feelings**: Calm, Vintage. An example is previous content like `realitywave <https://www.youtube.com/watch?v=QfLXRnAuV0g>`_
- **Approach**: CShade values uniformity, simplicity, and precision. A Sans-Serif \(Geometric, Rounded\) font encourages feelings of softness and friendliness.
- **Personalization**: Personalize thumbnail fonts to the subject of the video. Use `Pimp my Types Font Friday <https://pimpmytype.com/fontfriday/>`_ as a resource.

Tools & Resources
-----------------

.. list-table:: Software
  :stub-columns: 1

  * - To Edit Audio
    - *Audacity*
    - `<https://www.audacityteam.org/>`_
  * - To Edit Video
    - *DaVinci Resolve*
    - `<https://www.blackmagicdesign.com/products/davinciresolve>`_
  * - To Convert
    - *FFmpeg*
    - `<https://ffmpeg.org/>`_
  * - To Collect
    - *yt-dlp*
    - `<https://github.com/yt-dlp/yt-dlp>`_
  * - To Record
    - *OBS Studio*
    - `<https://obsproject.com/>`_
  * - Video Assets
    - Template
    - :download:`Video Asset Templates <../_static/youtube_template.zip>`

.. list-table:: Design
  :stub-columns: 1

  * - Light Color
    - *Ghost White*
    - #F8F8FF
  * - Dark Color
    - *Oil Black*
    - #0C0C0C
  * - Default Font
    - *Asap Medium*
    - `<https://fonts.google.com/specimen/Asap>`_
  * - Other Fonts
    - *Pimp my Type*
    - `<https://pimpmytype.com/fontfriday/>`_

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
