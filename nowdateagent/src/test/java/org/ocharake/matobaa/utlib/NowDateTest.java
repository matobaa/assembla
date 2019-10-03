package org.ocharake.matobaa.utlib;

import java.util.Calendar;
import java.util.Date;

import junit.framework.TestCase;

public class NowDateTest extends TestCase {

    public void testDateInstrument() {
        NowDateMockAgent.setExpected(100);
        assertEquals(100, new Date().getTime());
    }

    public void testCalenderInstrument() {
        NowDateMockAgent.setExpected(100);
        assertEquals(100, Calendar.getInstance().getTimeInMillis());
    }

    public static void main(String args[]) {
    	NowDateTest me = new NowDateTest();
    	me.testDateInstrument();
    	me.testCalenderInstrument();
    }

}
