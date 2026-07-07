/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  images: {
    unoptimized: true,
  },
  // Generous headroom for slow/sandboxed build environments where the
  // static-generation worker process can take a while to report back.
  staticPageGenerationTimeout: 180,
};

export default nextConfig;
