#!/usr/bin/env python
# coding: utf-8

import socket
import time

class data_transfer():
    """
    ソケット通信を用いて設備とデータ授受を行う。

    Parameters
    ----------
    host : string
        PLCのIPアドレス
    port : string
        PLCとの通信で用いるポート番号
    mode : string
        PLCとの通信方法（TCP または UDP）
    timeout : int
        PLCとの通信のタイムアウト。標準は3秒
    """
    def __init__(self, host, port, mode='UDP', timeout=3):
        try:
            if mode == 'UDP':
                self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            elif mode == 'TCP':
                self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            else:
                print('mode should be UDP or TCP')
                pass
            self.__sock.connect((host, port))
            self.__sock.settimeout(timeout)
        except socket.error:
            print("socket.error : can't establish connection!!\ncheck cable, plc, power etc...")

    def __del__(self):
        return self.close()
            
    def close(self):
        """
        ソケット通信を終了させる。
        
        Returns
        -------
        return_cd : int
            0 : 正常終了
            1 : 異常終了
        """
        return_cd = 0
        try:
            self.__sock.close()
        except socket.error:
            print("socket.error : can't close connection!!")
            return_cd = 1
        finally:
            return return_cd

    def send(self, cmd):
        """
        PLCに対してコマンドを送信する。

        Parameters
        ----------
        cmd : string
            PLCのコマンド（メーカーのマニュアルを参照のこと）
        
        Returns
        -------
        return_cd : int
            0 : 正常終了
            1 : 異常終了
        """
        return_cd = 0
        try:
            self.__sock.send(cmd.encode('utf-8'))
        except:
            return_cd = 1
        finally:
            return return_cd
        
    def recv(self):
        """
        PLCの応答を受け取る

        Returns
        -------
        return_cd : int
            0 : 正常終了
            1 : 異常終了
        data : list
            PLCの応答結果
        """
        return_cd = 0
        data=[]
        try:
            data=(self.__sock.recv(1024)).decode('utf-8')
        except:
            return_cd = 1
        finally:
            return return_cd, data
    
    def read(self, device, length=1):
        """
        PLCの指定されたデバイスのデータを取得する。
        内部で、send(), recv() 関数を利用している。

        Parameters
        ----------
        device : string
            取得するデータの番地
        length : int
            取得するデータの長さ

        Returns
        -------
        data : list
            取得したデータ
        """
        number=str(length).zfill(4)
        cmd = '001004010000'+device+number
        cmd_length = format(len(cmd), 'x').zfill(4)
        cmd=('500000FF03FF00' + cmd_length + cmd).upper()

        try:
            data = []
            if self.send(cmd) != 0:
                print('reading : send error!!')
                raise Exception
            rtn_cd, recv_data = self.recv()
            retry_cntr = 0
            while rtn_cd != 0:
                time.sleep(0.01)
                retry_cntr += 1
                rtn_cd, recv_data = self.recv()
                if retry_cntr > 0:
                    print('reading : recv error!!')
                    raise Exception
            if recv_data[18:22] != '0000':
                print('reading : data error!!')
                return [[None]]
            for i in range(length):
                pos = 4*i+22
                if recv_data[pos:pos+4] != '':
                    data.append(int(recv_data[pos:pos+4],16))
                else:
                    data.append('')
            return data
        except Exception as e:
            print("socket.read : exception args:", e.args)
            return [[e]]
    
    def write(self, device, data, length=1):
        """
        PLCの指定されたデバイスにデータを書き込む。
        内部で、send(), recv() 関数を利用している。

        Parameters
        ----------
        device : string
            取得するデータの番地
        data : string
            書き込むデータ（10進数表記）
        length : int
            取得するデータの長さ

        Returns
        -------
        return_cd : int
            0 : 正常終了
            1 : 異常終了
        """
        number=str(length).zfill(4)
        data=format(data, 'x').zfill(4)
        cmd = '001014010000'+device+number+data
        cmd_length = format(len(cmd), 'x').zfill(4)
        cmd=('500000FF03FF00' + cmd_length + cmd).upper()

        try:
            if self.send(cmd) != 0:
                print('writing : send error!!')
                raise Exception
            rtn_cd, recv_data = self.recv()
            retry_cntr = 0
            while rtn_cd != 0:
                time.sleep(0.01)
                retry_cntr += 1
                rtn_cd, recv_data = self.recv()
                if retry_cntr > 0:
                    print('writing : recv error!!')
                    raise Exception
            if recv_data[18:22] != '0000':
                print('writing : data error!!')
                return 1
            return 0
        except Exception as e:
            print("socket.write : exception args:", e.args)
            return e