Resource: Project/path/to/src/org/example/package/Class.java
Resource: Project/path/to/src/org/example/package/Class.java Line: 123
という文字列をリポジトリへのリンクにする機能:

1. まずそのままリポジトリを探してみる。
2. /trunk/ を頭につけて探してみる。
3. Wiki/TeamProjectSet に添付された projectSet.psf という
   チームプロジェクトセットファイルを参考に、パスを組み立てて探してみる。
   psf内のリポジトリパスに、/path/to/... を連結し、 頭からパス要素を
   切り取りながらリポジトリ内でファイルを探す。

リポジトリ内にファイルが見つかればリンクがつながる。
なければミッシングリンクになる。

----
org.example.package.Class.method(Class.java:123)
(未実装)

プロジェクトに .classpath がある場合は、
そのなかの <classpath>/<classpathentry kind="src" を探す。

ソースの場所が見つかったら、Resource: の 1. 2. 3. の要領でリポジトリリンクを探す。

ない場合は、MultiRepoSearchプラグインがあれば、そのリンクを生成する。

ない場合は、ミッシングリンクになる。