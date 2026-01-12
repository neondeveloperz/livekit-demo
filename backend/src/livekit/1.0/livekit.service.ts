import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { AccessToken, RoomServiceClient } from 'livekit-server-sdk';

@Injectable()
export class LiveKitService {
    private roomService: RoomServiceClient;

    constructor(private configService: ConfigService) {
        const url = this.configService.get<string>('LIVEKIT_URL') || '';
        const apiKey = this.configService.get<string>('LIVEKIT_API_KEY') || '';
        const apiSecret = this.configService.get<string>('LIVEKIT_API_SECRET') || '';

        this.roomService = new RoomServiceClient(url, apiKey, apiSecret);
    }

    async createToken(participantName: string, roomName: string) {
        const apiKey = this.configService.get<string>('LIVEKIT_API_KEY') || '';
        const apiSecret = this.configService.get<string>('LIVEKIT_API_SECRET') || '';

        const at = new AccessToken(apiKey, apiSecret, {
            identity: participantName,
        });

        at.addGrant({
            roomJoin: true,
            room: roomName,
            canPublish: true,
            canSubscribe: true,
        });

        return await at.toJwt();
    }

    async listRooms() {
        return this.roomService.listRooms();
    }
}