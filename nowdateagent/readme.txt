���ݎ������x(����)��javaAgent

=== ����͂Ȃ�? ===

Java���s���Ɋ��荞��ŁA���ݎ������擾����API��������܂��B
�}�V�������ɂ�����炸�A���[�U���v���O�����Ŗ����I�Ɏw�肵��������Ԃ��܂��B
���Ƃ��΁A�v���O�������� NowDateMockAgent.setExpected(86400); �Ƃ��ƁA
new java.util.Date() �͌��ݎ����ł͂Ȃ��A�K�� 1970-01-02T00:00Z ��Ԃ��悤�ɂȂ�܂��B

=== �ˑ�������� ===

�{�̃R�[�h�� javassist �Ɉˑ����܂��B
�e�X�g�R�[�h�� junit �Ɉˑ����܂��B

javassit-3.12.1-GA ����� junit-4.8.1 �œ���m�F���Ă��܂����A�Â��R�[�h���@��N�����ē���m�F�����̂ŁA����ȑO�̃o�[�W�����ł������炭���삵�܂��B

�Ȃ��A���̃��C�u������ MT-safe�ł͂���܂���B

=== �g���� ===

java.exe �Ɉȉ��̃I�v�V������ǉ����ċN�����Ă�������:
-bootclasspath javassist.jar
-javaagent:nowdateagent.jar

�N����:
java.exe -bootclasspath javassist.jar -javaagent:nowdateagent.jar \
    -classpath junit-4.8.2.jar org.ocharake.matobaa.utlib.NowDateTest

API:
NowDateMockAgent.setExpected(long)