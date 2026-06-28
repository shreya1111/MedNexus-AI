import { Schema, model, Document, Types } from 'mongoose';
import bcrypt from 'bcryptjs';

export interface IUser extends Document {
  _id: Types.ObjectId;
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  role: 'patient' | 'doctor' | 'admin';
  avatar?: string;
  isActive: boolean;
  isEmailVerified: boolean;
  refreshTokens: string[];
  lastLogin?: Date;
  createdAt: Date;
  updatedAt: Date;
  comparePassword(candidate: string): Promise<boolean>;
  fullName: string;
}

const userSchema = new Schema<IUser>(
  {
    email: { type: String, required: true, unique: true, lowercase: true, trim: true },
    password: { type: String, required: true, minlength: 8, select: false },
    firstName: { type: String, required: true, trim: true },
    lastName: { type: String, required: true, trim: true },
    role: { type: String, enum: ['patient', 'doctor', 'admin'], default: 'patient' },
    avatar: String,
    isActive: { type: Boolean, default: true },
    isEmailVerified: { type: Boolean, default: false },
    refreshTokens: { type: [String], select: false },
    lastLogin: Date,
  },
  {
    timestamps: true,
    toJSON: {
      virtuals: true,
      transform(_doc: unknown, ret: Record<string, unknown>) {
        ret['password'] = undefined;
        ret['refreshTokens'] = undefined;
        ret['__v'] = undefined;
        return ret;
      },
    },
  }
);

userSchema.virtual('fullName').get(function () {
  return `${this['firstName']} ${this['lastName']}`;
});

userSchema.pre<IUser>('save', async function (next) {
  if (!this.isModified('password')) return next();
  this.password = await bcrypt.hash(this.password, 12);
  return next();
});

userSchema.methods['comparePassword'] = async function (candidate: string): Promise<boolean> {
  return bcrypt.compare(candidate, this['password'] as string);
};

export const User = model<IUser>('User', userSchema);
