======
dontwi
======

About
======

dontwi_ is a status transporter script from Mastodon instances to Twitter. 
It transports statuses trigered by hashtag in Mastodon public time line to a twitter account. 
It's aime is communication with mastodon users and the twitter's follers. 

.. _dontwi: https://github.com/vocalodon/dontwi

Features
--------

- It supports CentOS 7.4 and Windows 10 with Python 3.4 and higher.
- Easily to use with cron. It transports only one status each run. 
- Statues with the specified tag in mastodon public local timeline are transferred.
- Long text in mastodon status is truncated to fit for twitter.
- Username at mastodon is attached in twitter status. 
- The attatched image is also transported with status text.
- Statuses once transferred are logged in the database and will not be transferred again.

Installation
============

This product is not yet in the python package.
Please put files to your working directory and edit configuration file named as  "dontwi.ini".
More installation information will be coming soon.

License
=======

Copyright  2017 `A.しおまねき(acct:a_shiomaneki@vocalodon.net)`_

Dontwi is licensed under the `GNU General Public License v3.0`_.
See `LICENSE`_ for the troposphere full license text.

.. _`GNU General Public License v3.0`: https://www.gnu.org/licenses/gpl-3.0.en.html
.. _`LICENSE`: https://github.com/vocalodon/dontwi/blob/master/LICENSE
.. _`A.しおまねき(acct:a_shiomaneki@vocalodon.net)`: https://vocalodon.net/@a_shiomaneki


Acknowledgements
================

- `左手(acct:lefthand666@vocalodon.net)`_, `TOMOKI++(acct:tomoki@vocalodon.net)`_ and users in `vocalodon.net`_ for original ideas and a lot of motivation.
- `TOMOKI++(acct:tomoki@vocalodon.net)`_ for providing the server and testing.
- `rainyday(acct:decoybird@vocalodon.net)`_ for providing initial OAuth code.

.. _`左手(acct:lefthand666@vocalodon.net)`: https://vocalodon.net/@lefthand666
.. _`TOMOKI++(acct:tomoki@vocalodon.net)`: https://vocalodon.net/@tomoki
.. _`rainyday(acct:decoybird@vocalodon.net)`: https://vocalodon.net/@decoybird
.. _`vocalodon.net`: https://vocalodon.net

