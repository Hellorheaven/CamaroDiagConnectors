using System.IO.Ports;
using System.Text.RegularExpressions;
using CamaroDiagConnectors.Windows;

if (args is ["--self-test"])
    return SelfTests.Run();

if (!OperatingSystem.IsWindows() || args.Length != 2 || args[0] != "--port" ||
    !Regex.IsMatch(args[1], @"\ACOM[1-9][0-9]{0,3}\z", RegexOptions.IgnoreCase | RegexOptions.CultureInvariant))
{
    Console.Error.WriteLine("Usage (isolated prototype only): --port COM5 | --self-test");
    return 2;
}
try
{
    using var serial=new SerialPort(args[1],115200,Parity.None,8,StopBits.One)
    {
        Handshake=Handshake.None, DtrEnable=true, RtsEnable=false,
        ReadTimeout=1500, WriteTimeout=1500
    };
    serial.Open();
    foreach(var response in new BinaryDiscovery(serial.BaseStream).Verify())
        Console.WriteLine(response);
    Console.WriteLine("Prototype discovery only; device not cryptographically authenticated.");
    return 0;
}
catch(Exception ex) when(ex is IOException or TimeoutException or UnauthorizedAccessException or InvalidOperationException)
{
    Console.Error.WriteLine("Discovery failed: "+ex.Message);
    return 1;
}
