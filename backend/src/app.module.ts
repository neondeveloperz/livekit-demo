import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { LiveKitModule } from './livekit/livekit.module';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
    }),
    LiveKitModule,
  ],
  controllers: [],
  providers: [],
})

export class AppModule { }
