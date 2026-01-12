import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { LiveKitController } from './1.0/livekit.controller';
import { LiveKitService } from './1.0/livekit.service';

@Module({
    imports: [ConfigModule],
    controllers: [LiveKitController],
    providers: [LiveKitService],
})
export class LiveKitModule { }