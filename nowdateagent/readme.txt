現在時刻を騙(かた)るjavaAgent

=== これはなに? ===

Java実行環境に割り込んで、現在時刻を取得するAPIを乗っ取ります。
マシン時刻にかかわらず、ユーザがプログラムで明示的に指定した時刻を返します。
たとえば、プログラム中で NowDateMockAgent.setExpected(86400); とやると、
new java.util.Date() は現在時刻ではなく、必ず 1970-01-02T00:00Z を返すようになります。

=== 依存するもの ===

本体コードは javassist に依存します。
テストコードは junit に依存します。

javassit-3.12.1-GA および junit-4.8.1 で動作確認していますが、古いコードを掘り起こして動作確認したので、それ以前のバージョンでもおそらく動作します。

なお、このライブラリは MT-safeではありません。

=== 使い方 ===

java.exe に以下のオプションを追加して起動してください:
-bootclasspath javassist.jar
-javaagent:nowdateagent.jar

起動例:
java.exe -bootclasspath javassist.jar -javaagent:nowdateagent.jar \
    -classpath junit-4.8.2.jar org.ocharake.matobaa.utlib.NowDateTest

API:
NowDateMockAgent.setExpected(long)