package org.ocharake.matobaa.utlib;

import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.lang.instrument.ClassFileTransformer;
import java.lang.instrument.IllegalClassFormatException;
import java.lang.instrument.Instrumentation;
import java.security.ProtectionDomain;

import javassist.ClassPool;
import javassist.CtClass;
import javassist.CtConstructor;

public class NowDateMockAgent {
	/**
	 * Key string in system properties. You can specify expected epoch date at
	 * system property.
	 */
	public static final String KEY = NowDateMockAgent.class.getCanonicalName()
			+ ".expectedDate";

	public static void premain(String agentArgs, Instrumentation instrumentation) {
		instrumentation.addTransformer(new DateTransformer());
	}

	public static void setExpected(long arg) {
		System.setProperty(KEY, Long.toString(arg));
	}

	public static long getExpected() {
		return Long.parseLong(System.getProperty(KEY));
	}

	static {
		System.setProperty(KEY, "0"); // proof
	}

}

class DateTransformer implements ClassFileTransformer {

	static String t = "Long.parseLong(System.getProperty(\""
			+ NowDateMockAgent.KEY + "\"));";

	public byte[] transform(ClassLoader void1, String className,
			Class<?> void2, ProtectionDomain void3, byte[] classfile)
			throws IllegalClassFormatException {
		try {
			// insert "time=t" at end of
			// GregorianCalengar.<init>(TimeZone,Locale)
			if (className.equals("java/util/GregorianCalendar")) {
				ClassPool pool = ClassPool.getDefault();
				InputStream stream = new ByteArrayInputStream(classfile);
				CtClass targetType = pool.makeClass(stream);
				CtClass[] paramTypes = pool.get(new String[] {
						"java/util/TimeZone", "java/util/Locale" });
				CtConstructor constructor = targetType
						.getDeclaredConstructor(paramTypes);
				constructor.insertAfter("time=" + t);
				return targetType.toBytecode();
			}
			// insert "fastTime=t" at end of java.util.Date.<init>()
			if (className.equals("java/util/Date")) {
				ClassPool pool = ClassPool.getDefault();
				InputStream stream = new ByteArrayInputStream(classfile);
				CtClass targetType = pool.makeClass(stream);
				targetType.getDeclaredConstructor(new CtClass[0]).insertAfter(
						"fastTime=" + t);
				return targetType.toBytecode();
			}
		} catch (Exception initCause) {
			IllegalClassFormatException e = new IllegalClassFormatException();
			e.initCause(initCause);
			throw e;
		}
		return null;
	}
}