======
dontwi
======

概要
======

dontwi_ はMastodonのハッシュタグ付きのstatus [#about_status]_ をTwitterに転送するスクリプトです．

転送トリガーには固定ハッシュタグ`#don_tw`と，他にお好みのハッシュタグを設定することができます．
dontwiは，これらのハッシュタグが付いたstatusを公開ローカルタイムラインから見つけて転送を行います．

Twitterに投稿する際にはMastodonにおけるユーザー名と`#don_tw`が付記されます．
このハッシュタグを付ける目的は，Twitter上でこのハッシュタグによる擬似的な連合を形成するすることです．
この狙いについては `TOMOKI++(@tomoki@vocalodon.net)`_ が `Mastodon 2 Advent Calendar 2017`_  でが説明しています．

.. [#about_status] Twitterにおけるツイート，Mastodonにおけるトゥートは，APIドキュメント内でstatusと表現されています．

.. _dontwi: https://github.com/vocalodon/dontwi
.. _`Mastodon 2 Advent Calendar 2017`: http://info.vocalodon.net/notes/dontwi.html

特徴
--------

- dontwi は Python 3.4 以上， CentOS 7.4および Windows 10をサポートします．
- ``cron`` と共に使うと便利です．起動毎に1つのstatusを転送します. 
- 指定されたハッシュタグを持つstatusを公開ローカルタイムラインから見つけて転送を行います．
- Mastodonに投稿された長いテキストはTwitterの制限に合わせて切り詰めまれます．
- Twitterに投稿されるstatusにはMastodonにおけるユーザー名が付記されます．
- 添付された画像ファイルも一緒に転送されます.
- 転送したstatusを記録しテイルので，一度転送されたstatusが再び転送されることはありません，

どのように動くのか
==================

dontwiはMastodonのローカルタイムラインにある指定されたハッシュタグをもつstatusを転送します．例えばMastodonに投稿されたFig.1 のstatusはTwitterにFig.2のように投稿されます．

.. image:: images/sample_toot.png

Fig.1 Sample status on Mastodon

.. image:: images/result_tweet.png

Fig.2 Transported status on Twitter

dontwiは実行毎にMastodon APIを用いてはハッシュタグタイムラインを取得します．指定のハッシュタグもしくは``#don_tw``がついたstatusを見つけると，まずこれらをログDBに保存します．

次にログDBにある最も古いstatusを取り出し，TwitterにAPIを用いて投稿します．このstatusには投稿者のMastodonにおけるアドレスとハッシュタグ``#don_tw``が付記されます．
statusに添付されたメディアファイル [#f1]_ もTwitterの制約に合わせてリサイズしてから一緒に投稿されます．

All of the contents that are text, link address, and hashtag are kept if the number of characters is within 280, which is the limit of Twitter. When the length exceeds the limit, dontwi trims text without modification link and hashtag as much as possible.

``#don_tw`` hashtag appended to the post to Twitter is not configurable. The reason why is aiming to organize federation timeline like Mastodon's one on Twitter by this fixed hashtag. If you want to use another hashtag, you can do by modification to source code directory. However, we hope you keep this hashtag for the federation timeline on Twitter.

.. [#f1] This is currently only available for image files.


インストール
============

pip3を用いてこのレポジトリにあるパッケージを簡単にインストールすることができます::

    pip3 install https://github.com/vocalodon/dontwi/releases/download/v1.0.0/dontwi-1.0-py3-none-any.whl

``setup.py`` を用いてローカルのレポジトリからインストールすることもできます::

    python3 setup.py install

設定
==========

1. 設定ファイルを用意する
--------------------------------

設定ファイル ``dontwi.ini`` を ``/etc`` に置いてください. ``dontwi.ini`` の検索パスは ``/etc`` aとカレントディレクトリです．設定ファイルのテンプレート `examples/dontwi.ini`_ はこんな感じです::

    [operation]
    inbound = your_mastodon
    trigger = hashtag:your_hashtag
    outbound = dontwi

    [endpoint your_mastodon]
    type = mastodon
    api_base_url = https://your_mastodon.domain
    client_name = dontwi
    since = 

    [endpoint dontwi]
    type = twitter
    app_key = 
    app_secret = 
    oauth_token = 
    oauth_token_secret = 
    message_length = 280

    [result log]
    db_file = /var/db/dontwi_log.db

..  _`examples/dontwi.ini`: examples/dontwi.ini

2. インスタンスに合わせて設定を変更する
-----------------------------------------

``dontwi.ini`` をあなたのMastodonインスタンスとTwitterアカウントに合わせて変更してください　へ account. 設定が必用な最小限のパラメータは以下の通りです．
なお，設定ファイル中にはコメントを書かない方が良いです．れは，Mastodonのクラインアントキーを保存する際にコメントが削除されてしまうからです．

``operation`` セクション
+++++++++++++++++++++++++

``inbound``
    発信元の定義が書かれているのセクション名

    このセクション名は変更することができますが，ここの記述と発信元の定義を定めているセクション名の対応関係は維持してください．       

``trigger``
    検出トリガーとするハッシュタグ

    ハッシュタグの前にはプレフィックス``hashtag:``を付けてください．またハッシュタグの ``#`` は抜いて記述してください．

``outbound``
    着信先の定義が書かれているセクション名

    着信先の定義について ``inbound`` の場合と同様に記述してください．

``endpoint your_mastodon`` セクション
+++++++++++++++++++++++++++++++++++++

``type``
    Type name of the endpoint

    Set ``mastodon``. In the future, we may implement another type support. 

``api_base_url``
    Set base URL of your Mastodon instance.

``client_name``
    Client name at API access

``endpoint dontwi`` セクション
++++++++++++++++++++++++++++++

``type``
    Type name of the endpoint

    Set ``twitter``. In the future, we may implement another type support.

``app_key``, ``app_secret``, ``oauth_token``, ``oauth_token_secret``
    Set Twitter API key and related parameters. dontwi uses Twython_ library to access to Twitter. Please refer Twython's documents to obtain these keys.  

.. _Twython: https://github.com/ryanmcgrath/twython

``result log`` セクション
+++++++++++++++++++++++++

``db_file`` 
    Log DB file path

    Set log DB file path. Default is ``dontwi_log.db`` on current directory. We recommend using ``/var/db/dontwi_log.db`` according to FHS_.

.. _FHS: https://wiki.linuxfoundation.org/lsb/fhs

3. 設定の確認
---------------------------

You can confirm dontwi installation by a test run with ``--help`` option  via::

    [root@centos7 opt]# dontwi --help
    usage: dontwi [-h] [--config-file CONFIG_FILE] [--summary] [--trigger TRIGGER]
              [--since SINCE] [--until UNTIL] [--limit LIMIT] [--dry-run]
              [--get-secret] [--dump-status-strings] [--dump-log]
              [--dump-log-readable] [--remove-waiting] [--remove-wrong]
              [--db-file DB_FILE]

    A status transporter from Mastodon to Twitter

    optional arguments:
      -h, --help            show this help message and exit
      --config-file CONFIG_FILE
                        Using CONFIG_FILE instead of the default.
      --summary             Showing summary of log DB
      --trigger TRIGGER     Using TRIGGER instead of trigger in the config file
      --since SINCE         Using SINCE instead of since in the config file
      --until UNTIL         Using UNTIL instead of until in the config file
      --limit LIMIT         Using LIMIT instead of limit in the config file
      --dry-run             Getting the last status with the hashtag, but don't
                        send status to outbound service.
      --get-secret          Getting the access keys and others from Mastodon
                        instance and saving these in the config file.
      --dump-status-strings
                        Dumping status strings to be marked as 'Waiting'
                        status
      --dump-log            Dumping all records in the log database.
      --dump-log-readable   Dumping all records in the log database in a human-
                        readable format.
      --remove-waiting      Removing records in 'Waiting' from the database
      --remove-wrong        Removing records in 'Waiting' from the database
      --db-file DB_FILE     Using log DB_FILE instead of db_file of [result log]
                        section in the config file.


If some installation problems remain, you see the error message at above test.

For confirmation of ``dontwi.ini``,  run ``dontwi`` with ``--dry-run`` via::

    [root@centos7 ~]# dontwi --dry-run
    Test at 2018-02-17T14:04:05.826111+00:00 in:your_mastodon,4705377 out:, tag:どんつい

When first accessing to your Mastodon instance, dontwi saves the access keys in ``config.ini``. 

When you execute dontwi with ``--dry-run``,  dontwi gets a tag timeline of your Mastodon instance via `Timelines API`_ and prepares statuses to Twitter. dontwi prepares to post the oldest status in API response to Twitter, however, does not until post. This process is logged with 'Test' label. Other status texts are queued for next run with 'Waiting' label. While remaining in the queue, post one status from the queue on each run.

.. _`Timelines API`: https://github.com/tootsuite/documentation/blob/master/Using-the-API/API.md#timelines

You can see the number of these labels in the log DB by ``--summary`` option via::

    [root@centos7 opt]# dontwi --summary
    dontwi version  1.0
    log db  {'application': 'dontwi', 'version': '1.0'}
    record number   25
    Start   0
    Waiting 23
    Succeed 0
    Failed  0
    Test    2

Because labeled entries not specified with ``Waiting`` will not be processed, so delete the ``Test`` entries using ``--remove-wrong`` option before starting operation.::

    [root@centos7 opt]# dontwi --remove-wrong

In this process, other failure-related entries will be deleted.

After the above preparation, you can test run. Simply execute ``dontwi``::

    [root@centos7 ~]# dontwi
    Succeed at 2018-02-17T14:04:05.826111+00:00 in:your_mastodon,4705377 out:, tag:どんつい

4. ``dontwi`` のエントリーをcrontabに加える
----------------------------------------------

Let's add dontwi entry to crontab. Examaple is below::

    */2  *  *  *  * root       /usr/bin/dontwi

Above entry means run dontwi each 2 minute. Also, refer `examples/crontab`_. If you prefer ``systemd``, you can use `examples/dontwi.service`_ and `examples/dontwi.timer`_.

.. _`examples/crontab`: examples/crontab
.. _`examples/dontwi.service`: examples/dontwi.service
.. _`examples/dontwi.timer`: examples/dontwi.timer

ライセンス
===========

Copyright  2017 `A.しおまねき(@a_shiomaneki@vocalodon.net)`_

Dontwi is licensed under the `GNU General Public License v3.0`_.
See `LICENSE`_ for the troposphere full license text.

.. _`GNU General Public License v3.0`: https://www.gnu.org/licenses/gpl-3.0.en.html
.. _`LICENSE`: https://github.com/vocalodon/dontwi/blob/master/LICENSE
.. _`A.しおまねき(@a_shiomaneki@vocalodon.net)`: https://vocalodon.net/@a_shiomaneki

謝辞
================

- `左手(@lefthand666@vocalodon.net)`_ さん, `TOMOKI++(@tomoki@vocalodon.net)`_ さんと`vocalodon.net`_ のユーザーの皆様からは元となったアイディアとモチベーションを頂いたとこ，感謝申し上げます．．
- `TOMOKI++(@tomoki@vocalodon.net)`_ for providing the server and testing.
- `rainyday(@decoybird@vocalodon.net)`_ for providing initial OAuth code.

.. _`左手(@lefthand666@vocalodon.net)`: https://vocalodon.net/@lefthand666
.. _`TOMOKI++(@tomoki@vocalodon.net)`: https://vocalodon.net/@tomoki
.. _`rainyday(@decoybird@vocalodon.net)`: https://vocalodon.net/@decoybird
.. _`vocalodon.net`: https://vocalodon.net