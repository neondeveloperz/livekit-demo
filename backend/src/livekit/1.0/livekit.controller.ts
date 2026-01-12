import { Controller, Get, Query } from '@nestjs/common';
import { LiveKitService } from './livekit.service';

@Controller('livekit')
export class LiveKitController {
    constructor(private readonly livekitService: LiveKitService) { }

    @Get('token')
    async getToken(
        @Query('room') room: string,
        @Query('username') username: string,
    ) {
        // ในความเป็นจริง ควรตรวจสอบ Auth ของ User ก่อน (UseGuards)
        const token = await this.livekitService.createToken(username, room);
        return { token };
    }

    @Get('rooms')
    async getRooms() {
        return this.livekitService.listRooms();
    }
}