'use client';

import { handleLogin } from '@/actions/login';
import Image from 'next/image';
import { useForm } from 'react-hook-form';

export type AuthFormData = {
  email: string;
  password: string;
};

const Auth = () => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<AuthFormData>();

  const onSubmit = (formData: AuthFormData) => {
    handleLogin(formData);
  };

  return (
    <section className='h-screen-wo-topbar flex w-full'>
      <div className='flex w-3/10 flex-col items-start justify-start px-16 pt-20'>
        <h1 className='font-bebas-neue mb-8 text-5xl font-bold text-neutral-800'>
          LOGOWANIE
        </h1>
        <form
          onSubmit={handleSubmit(onSubmit)}
          className='flex w-full flex-col items-start justify-start gap-4'>
          <input
            type='email'
            className='h-12 w-full rounded-md border-2 border-black px-2'
            placeholder='E-mail'
            {...register('email')}
          />
          <input
            type='password'
            className='h-12 w-full rounded-md border-2 border-black px-2'
            placeholder='Hasło'
            {...register('password')}
          />
          <button
            type='submit'
            className='bg-custom-red font-bebas-neue my-4 h-12 w-40 rounded-md text-xl font-bold text-white'>
            ZALOGUJ
          </button>
        </form>
      </div>
      <div className='relative z-0 w-7/10 overflow-hidden object-contain shadow-[0_0_10px_1px_black]'>
        <Image
          src='/auth_bg.png'
          alt='background'
          fill={true}
        />
      </div>
    </section>
  );
};

export default Auth;
