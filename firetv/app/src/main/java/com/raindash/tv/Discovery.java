package com.raindash.tv;

import android.content.Context;
import android.net.DhcpInfo;
import android.net.wifi.WifiManager;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.SocketTimeoutException;
import java.nio.charset.Charset;

/** Finds the PC running Rain World + RainDash: broadcast "RAINDASH_DISCOVER", the mod answers with its URL. */
final class Discovery {
    static final int PORT = 47812;

    private Discovery() {
    }

    /** Returns the dashboard URL, or null if nothing answered within {@code timeoutMs}. Blocking. */
    static String find(Context context, int timeoutMs) {
        Charset ascii = Charset.forName("US-ASCII");
        byte[] ask = "RAINDASH_DISCOVER".getBytes(ascii);
        try (DatagramSocket socket = new DatagramSocket()) {
            socket.setBroadcast(true);
            socket.setSoTimeout(timeoutMs);
            for (InetAddress target : targets(context)) {
                try {
                    socket.send(new DatagramPacket(ask, ask.length, target, PORT));
                } catch (Exception ignored) {
                    // try the next address
                }
            }
            byte[] buf = new byte[512];
            long deadline = System.currentTimeMillis() + timeoutMs;
            while (System.currentTimeMillis() < deadline) {
                DatagramPacket packet = new DatagramPacket(buf, buf.length);
                try {
                    socket.receive(packet);
                } catch (SocketTimeoutException e) {
                    return null;
                }
                String reply = new String(packet.getData(), 0, packet.getLength(), ascii).trim();
                if (reply.startsWith("RAINDASH ")) return MainActivity.normalize(reply.substring(9));
            }
        } catch (Exception ignored) {
            // no network
        }
        return null;
    }

    private static InetAddress[] targets(Context context) {
        InetAddress subnet = null;
        try {
            WifiManager wifi = (WifiManager) context.getApplicationContext().getSystemService(Context.WIFI_SERVICE);
            DhcpInfo dhcp = wifi != null ? wifi.getDhcpInfo() : null;
            if (dhcp != null && dhcp.ipAddress != 0) {
                int broadcast = (dhcp.ipAddress & dhcp.netmask) | ~dhcp.netmask;
                byte[] quads = new byte[4];
                for (int k = 0; k < 4; k++) quads[k] = (byte) ((broadcast >> (k * 8)) & 0xFF);
                subnet = InetAddress.getByAddress(quads);
            }
        } catch (Exception ignored) {
            // ethernet adapter or no Wi-Fi permission: global broadcast still works
        }
        try {
            InetAddress all = InetAddress.getByName("255.255.255.255");
            return subnet != null ? new InetAddress[]{subnet, all} : new InetAddress[]{all};
        } catch (Exception e) {
            return new InetAddress[0];
        }
    }
}
